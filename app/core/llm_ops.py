import os
import mlflow
import time
from functools import wraps
from typing import Any, Callable

# Initialize MLflow tracking to local directory with recovery
try:
    mlflow.set_tracking_uri("sqlite:///mlruns.db")
    mlflow.set_experiment("Athena_LLMOps")
except Exception as e:
    print(f"[MLFLOW RECOVERY] Resetting corrupted mlruns.db: {e}")
    if os.path.exists("mlruns.db"):
        try:
            os.remove("mlruns.db")
        except Exception:
            pass
    try:
        mlflow.set_tracking_uri("sqlite:///mlruns.db")
        mlflow.set_experiment("Athena_LLMOps")
    except Exception as ex:
        print(f"[MLFLOW LOG] Disabling MLflow tracking: {ex}")

def track_prompt_execution(prompt_version: str, task_name: str):
    """
    Decorator to wrap LLM invocations, logging the input, output, and execution latency to MLflow.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            with mlflow.start_run(run_name=f"{task_name}_{int(time.time())}") as run:
                mlflow.log_param("prompt_version", prompt_version)
                mlflow.log_param("task_name", task_name)
                
                # Log a sanitized version of inputs
                input_preview = str(kwargs.get("user_query", args[0] if args else "No input"))[:500]
                mlflow.log_param("input_preview", input_preview)
                
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    latency = time.time() - start_time
                    mlflow.log_metric("latency_seconds", latency)
                    
                    # Log output
                    output_preview = str(result)[:1000]
                    mlflow.log_text(output_preview, "output.txt")
                    
                    return result
                except Exception as e:
                    latency = time.time() - start_time
                    mlflow.log_metric("latency_seconds", latency)
                    mlflow.log_param("error", str(e))
                    raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            with mlflow.start_run(run_name=f"{task_name}_{int(time.time())}") as run:
                mlflow.log_param("prompt_version", prompt_version)
                mlflow.log_param("task_name", task_name)
                
                input_preview = str(kwargs.get("user_query", args[0] if args else "No input"))[:500]
                mlflow.log_param("input_preview", input_preview)
                
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    latency = time.time() - start_time
                    mlflow.log_metric("latency_seconds", latency)
                    
                    output_preview = str(result)[:1000]
                    mlflow.log_text(output_preview, "output.txt")
                    
                    return result
                except Exception as e:
                    latency = time.time() - start_time
                    mlflow.log_metric("latency_seconds", latency)
                    mlflow.log_param("error", str(e))
                    raise
                    
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
