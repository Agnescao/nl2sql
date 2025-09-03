import asyncio
import logging
from typing import List, Callable, Any, Optional
from dataclasses import dataclass
from enum import Enum
import time

"""“在Agent系统中，经常需要处理大量异步任务（如并行调用多个工具或模型）。请用你熟悉的语言（Python/Go/Java）伪代码实现一个简单的异步任务调度器，它可以并发执行多个任务，并收集所有结果。你会考虑哪些关键点来保证系统的健壮性和效率"""
class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TaskResult:
    task_id: str
    status: TaskStatus
    result: Any = None
    error: Optional[Exception] = None
    execution_time: float = 0.0


class AsyncTaskScheduler:
    def __init__(self, max_concurrent_tasks: int = 10, timeout: float = 30.0):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.timeout = timeout
        #  创建信号量 # 控制并发数量  主要在使用协程时，限制并发数量，避免同时执行过多任务导致资源消耗过多，那这个信号量就起作用了，那这个max_concurrent_tasks参数就是用来控制并发数量，如果max_concurrent_tasks的值为10，则表示最多允许同时执行10个任务。
        # 这样可以防止系统过载，提高系统的稳定性和响应速度。
        # 信号量的作用是限制并发数量，当并发数量达到最大值时，新的任务会被阻塞，直到有任务完成或者超时。
        # 这个max current tasks参数设置多少的取决因数有哪些，比如系统资源、任务复杂度、响应时间要求等。
        # 比如，如果一个任务需要10秒才能完成，而系统资源只有2个CPU核，则max_concurrent_tasks的值应该设置为2，这样最多只能同时执行两个任务。
        # 如果一个任务需要1秒才能完成，而系统资源有8个CPU核，则max_concurrent_tasks的值可以设置为8，这样可以充分利用系统资源，提高任务处理效率。
        # 如果一个任务需要5秒才能完成，而系统资源有4个CPU核，则max_concurrent_tasks的值可以设置为4，这样最多只能同时执行4个任务。
        # 一般企业中例如豆包产品的max_concurrent_tasks的值设置为10-20之间，这样可以保证系统的稳定性和响应速度，同时也能满足大部分任务的处理需求。
        #
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self.logger = logging.getLogger(__name__)

    async def execute_task(self, task_id: str, task_func: Callable, *args, **kwargs) -> TaskResult:
        """
        执行单个异步任务
        """
        start_time = time.time()
        try:
            async with self.semaphore:  # 控制并发数量
                self.logger.info(f"Starting task {task_id}")
                # 设置任务超时
                result = await asyncio.wait_for(
                    task_func(*args, **kwargs),
                    timeout=self.timeout
                )
                execution_time = time.time() - start_time
                self.logger.info(f"Task {task_id} completed successfully")
                return TaskResult(
                    task_id=task_id,
                    status=TaskStatus.COMPLETED,
                    result=result,
                    execution_time=execution_time
                )
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            error = TimeoutError(f"Task {task_id} timed out after {self.timeout} seconds")
            self.logger.error(f"Task {task_id} timed out")
            return TaskResult(
                task_id=task_id,
                status=TaskStatus.FAILED,
                error=error,
                execution_time=execution_time
            )
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Task {task_id} failed with error: {str(e)}")
            return TaskResult(
                task_id=task_id,
                status=TaskStatus.FAILED,
                error=e,
                execution_time=execution_time
            )

    async def schedule_tasks(self, tasks: List[tuple]) -> List[TaskResult]:
        """
        并发调度多个任务
        tasks: List of (task_id, task_func, args, kwargs) tuples
        """
        # 创建任务列表
        task_futures = [
            self.execute_task(task_id, task_func, *args, **kwargs)
            for task_id, task_func, args, kwargs in tasks
        ]

        # 并发执行所有任务
        results = await asyncio.gather(*task_futures, return_exceptions=True)

        # 处理异常情况
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                task_id = tasks[i][0] if i < len(tasks) else f"unknown_task_{i}"
                processed_results.append(TaskResult(
                    task_id=task_id,
                    status=TaskStatus.FAILED,
                    error=result,
                    execution_time=0.0
                ))
            else:
                processed_results.append(result)

        return processed_results


# 使用示例
async def sample_task(name: str, duration: float) -> str:
    """模拟异步任务"""
    await asyncio.sleep(duration)
    return f"Result from {name}"


async def main():
    scheduler = AsyncTaskScheduler(max_concurrent_tasks=3, timeout=5.0)

    # 定义任务列表
    tasks = [
        ("task_1", sample_task, ("Task1", 1.0), {}),
        ("task_2", sample_task, ("Task2", 2.0), {}),
        ("task_3", sample_task, ("Task3", 2.0), {}),
        ("task_4", sample_task, ("Task4", 1.0), {}),
    ]

    # 执行所有任务
    results = await scheduler.schedule_tasks(tasks)

    # 处理结果
    for result in results:
        if result.status == TaskStatus.COMPLETED:
            print(f"Task {result.task_id}: Success - {result.result}")
        else:
            print(f"Task {result.task_id}: Failed - {result.error}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
