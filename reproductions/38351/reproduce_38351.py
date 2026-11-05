"""CK01: execute unmodified LangChain graph with synthetic tool results.

Run with -B. Only the model's outputs and the application's middleware are fake;
LangChain/LangGraph graph construction, reducers and routing are untouched.
"""

import hashlib
import importlib.metadata
import importlib.util
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import tomllib
import traceback

REPO = Path(r"C:\D\projects\langchain")
SHA = "5893459c4f2bfac6c8d3262cae1e3f2246d9287f"
sys.dont_write_bytecode = True
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"
sys.path[:0] = [str(REPO / "libs/langchain_v1"), str(REPO / "libs/core")]


def emit(kind, **fields):
    print(json.dumps({"kind": kind, **fields}, ensure_ascii=False), flush=True)


def git(*args):
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
    env.update(GIT_OPTIONAL_LOCKS="0", GIT_NO_LAZY_FETCH="1", GIT_TERMINAL_PROMPT="0")
    return subprocess.run(
        ["git", "--no-pager", "--no-replace-objects", "-c", "core.fsmonitor=false",
         "-C", str(REPO), *args],
        check=True, capture_output=True, timeout=20, env=env,
    ).stdout


def snapshot():
    head = git("rev-parse", "HEAD").decode().strip()
    status = git("status", "--porcelain=v1", "--untracked-files=all").decode()
    result = {"head": head, "status": status, "is_dirty": bool(status)}
    emit("repository", **result)
    if head != SHA or status:
        raise RuntimeError("Repository must be clean at the approved SHA.")
    return result


def verify_source(path):
    path = Path(path).resolve()
    relative = path.relative_to(REPO).as_posix()
    actual = path.read_bytes()
    committed = git("show", f"{SHA}:{relative}")
    if actual.replace(b"\r\n", b"\n") != committed.replace(b"\r\n", b"\n"):
        raise RuntimeError(f"Source differs from approved commit: {relative}")
    return {"path": str(path), "sha256": hashlib.sha256(actual).hexdigest(),
            "matches_commit_text": True}


def summarize(messages):
    return [{"type": m.type, "id": m.id, "content": m.content,
             "tool_calls": getattr(m, "tool_calls", None),
             "tool_call_id": getattr(m, "tool_call_id", None)} for m in messages]


def main():
    snapshot()
    emit("python", executable=sys.executable, version=sys.version)
    lock = tomllib.loads((REPO / "libs/langchain_v1/uv.lock").read_text("utf-8"))
    emit("lockfile", **verify_source(REPO / "libs/langchain_v1/uv.lock"))
    locked = {p["name"]: p["version"] for p in lock["package"]}
    installed = {d.metadata["Name"]: d.version for d in importlib.metadata.distributions()}
    emit("installed_distributions", versions=installed)
    for name in ("langgraph", "langgraph-prebuilt", "langgraph-checkpoint", "pydantic"):
        if importlib.metadata.version(name) != locked[name]:
            raise RuntimeError(f"Installed version differs from lock: {name}")

    import langchain
    import langchain_core
    from langchain.agents import create_agent
    from langchain.agents.middleware.types import (
        AgentMiddleware, ExtendedModelResponse, ModelRequest, ModelResponse,
    )
    from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
    from langchain_core.tools import tool
    from langgraph.graph import _branch
    from langgraph.types import Command

    model_path = REPO / "libs/langchain_v1/tests/unit_tests/agents/model.py"
    emit("fake_model_source", **verify_source(model_path))
    spec = importlib.util.spec_from_file_location("ck01_fake_model", model_path)
    fake_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fake_module)
    model = fake_module.FakeToolCallingModel(tool_calls=[[
        {"name": "lookup", "args": {"value": "example"},
         "id": "call-38351", "type": "tool_call"},
    ], []])
    emit("loaded_sources", langchain=str(Path(langchain.__file__).resolve()),
         langchain_version=langchain.__version__,
         core=str(Path(langchain_core.__file__).resolve()),
         core_version=langchain_core.__version__,
         create_agent=inspect.getsourcefile(create_agent),
         middleware=inspect.getsourcefile(AgentMiddleware),
         graph_dispatch=str(Path(_branch.__file__).resolve()),
         langgraph_version=importlib.metadata.version("langgraph"),
         local_packages="langchain/core loaded directly from checkout; not installed distributions")
    if Path(inspect.getsourcefile(create_agent)).resolve() != (
        REPO / "libs/langchain_v1/langchain/agents/factory.py"
    ).resolve():
        raise RuntimeError("create_agent loaded from unexpected source.")
    if Path(langchain_core.__file__).resolve() != (
        REPO / "libs/core/langchain_core/__init__.py"
    ).resolve():
        raise RuntimeError("core loaded from unexpected source.")
    if langchain.__version__ != locked["langchain"] or langchain_core.__version__ != locked["langchain-core"]:
        raise RuntimeError("Local package version differs from lock.")

    counts = {"handler_calls": 0, "tool_calls": 0, "injected_messages": 0}

    @tool
    def lookup(value: str) -> str:
        """Return a deterministic local result for a value."""
        counts["tool_calls"] += 1
        emit("tool_executed", value=value)
        return "real-tool-result"

    class SyntheticToolResult(AgentMiddleware):
        def wrap_model_call(self, request: ModelRequest, handler) -> ModelResponse | ExtendedModelResponse:
            emit("middleware_before_handler", messages=summarize(request.messages))
            counts["handler_calls"] += 1
            response = handler(request)
            emit("middleware_after_handler", messages=summarize(response.result), model_calls=model.index)
            replies = []
            for message in response.result:
                if isinstance(message, AIMessage):
                    for call in message.tool_calls:
                        replies.append(ToolMessage(
                            content="synthetic-tool-result", name=call["name"],
                            tool_call_id=call["id"], id="tool-result-38351",
                        ))
            if not replies:
                return response
            counts["injected_messages"] += len(replies)
            emit("middleware_inject", messages=summarize(replies))
            return ExtendedModelResponse(
                model_response=response, command=Command(update={"messages": replies}),
            )

    agent = create_agent(model=model, tools=[lookup], middleware=[SyntheticToolResult()])
    # Verify every already-imported repository Python module before execution.
    paths = sorted({str(Path(m.__file__).resolve()) for m in tuple(sys.modules.values())
                    if getattr(m, "__file__", None)
                    and Path(m.__file__).suffix == ".py"
                    and Path(m.__file__).resolve().is_relative_to(REPO)})
    manifest = [verify_source(path) for path in paths]
    emit("source_manifest", files=manifest)
    emit("invoke_start", configuration="wrap_model_call only; no hooks or response_format")
    try:
        result = agent.invoke(
            {"messages": [HumanMessage(content="Look up example", id="human-38351")]},
            config={"recursion_limit": 10},
        )
    except Exception as error:
        branch_observations = []
        tb = error.__traceback__
        while tb:
            frame = tb.tb_frame
            if Path(frame.f_code.co_filename).resolve() == Path(_branch.__file__).resolve():
                item = {"function": frame.f_code.co_name, "line": tb.tb_lineno}
                route = frame.f_locals.get("result")
                if isinstance(route, (str, list, tuple)):
                    item["router_result"] = route
                branch = frame.f_locals.get("self")
                if getattr(branch, "ends", None) is not None:
                    item["registered_ends"] = branch.ends
                for key in ("value", "input"):
                    state = frame.f_locals.get(key)
                    if isinstance(state, dict) and "messages" in state:
                        item[key + "_messages"] = summarize(state["messages"])
                branch_observations.append(item)
            tb = tb.tb_next
        proven_route = any(o.get("router_result") in ("model", ["model"])
                           and "model" not in o.get("registered_ends", {"model": "model"})
                           for o in branch_observations)
        emit("exception", error_type=type(error).__name__, error=str(error),
             branch_observations=branch_observations)
        emit("result", classification=("成功重現" if isinstance(error, KeyError)
             and error.args == ("model",) and proven_route
             and counts["injected_messages"] == 1 else "其他執行期錯誤"),
             model_calls=model.index, **counts)
        raise
    else:
        emit("result", classification="未重現", messages=summarize(result["messages"]),
             model_calls=model.index, **counts)
    finally:
        snapshot()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
