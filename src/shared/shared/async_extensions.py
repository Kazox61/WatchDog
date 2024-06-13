import asyncio


def split_even(l: list, n: int) -> list[list]:
    k, m = divmod(len(l), n)
    return list(l[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))


async def run_tasks(tasks: list, batches=1, delay=1.0, delay_on_last=True):
    split_tasks = split_even(tasks, batches)
    for i, split_task in enumerate(split_tasks):
        await asyncio.gather(*split_task)

        if i == len(split_tasks) - 1 and not delay_on_last:
            continue

        await asyncio.sleep(delay)
