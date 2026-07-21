import os
import mlflow
import time
from functools import wraps
from typing import Any, Callable

try:
    os.makedirs("/tmp/mlflow", exist_ok=True)
    mlflow.set_tracking_uri("sqlite:////tmp/mlflow/mlruns.db")
    mlflow.set_experiment("Athena_LLMOps")
except Exception as e:
    print(f"[MLFLOW LOG] MLflow tracking bypassed: {e}")

def track_prompt_execution(prompt_version: str, task_name: str):
    """
    Decorator to wrap LLM invocations, logging execution latency safely without blocking.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                latency = time.time() - start_time
                try:
                    with mlflow.start_run(run_name=f"{task_name}_{int(time.time())}", nested=True):
                        mlflow.log_param("prompt_version", prompt_version)
                        mlflow.log_param("task_name", task_name)
                        mlflow.log_metric("latency_seconds", latency)
                except Exception:
                    pass
                return result
            except Exception as e:
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                latency = time.time() - start_time
                try:
                    with mlflow.start_run(run_name=f"{task_name}_{int(time.time())}", nested=True):
                        mlflow.log_param("prompt_version", prompt_version)
                        mlflow.log_param("task_name", task_name)
                        mlflow.log_metric("latency_seconds", latency)
                except Exception:
                    pass
                return result
            except Exception as e:
                raise

        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator

