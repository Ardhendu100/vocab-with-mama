import cProfile
import pstats
import asyncio

from main import send_daily_lesson


def run_profile():
    profiler = cProfile.Profile()

    profiler.enable()

    asyncio.run(send_daily_lesson())

    profiler.disable()

    stats = pstats.Stats(profiler)

    stats.sort_stats("cumulative")

    stats.print_stats(20)


if __name__ == "__main__":
    run_profile()