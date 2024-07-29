from fastapi import FastAPI
import matplotlib
import matplotlib.pyplot as plt
import math
from fastapi import Response, Request
import io
import settings
import sentry_sdk
import aiomcache
import hashlib


app = FastAPI()
matplotlib.use('agg')
cache_ttl = 86400
max_points = 200
sentry_sdk.init(dsn=settings.SENTRY_DSN)
image_formats = ["png", "webp"]
mc = aiomcache.Client("127.0.0.1", 11211)


class UnknownFormat(Exception):
    pass


@app.get("/favicon.ico", status_code=404)
async def favicon():
    return "Not found"


@app.get("/{data}.{ext}")
async def api(data, ext, request: Request, yticks: bool = False, hticks_start: int | None = None):
    if ext not in image_formats:
        raise UnknownFormat(f"UnknownFormat: {ext}")
    content = await cached_sparkline(request, parse_list(data), yticks=yticks, format=ext, hticks_start=hticks_start)
    return Response(content=content, media_type=f"image/{ext}")


def parse_list(data, cast_to=float):
    return [cast_to(p) for p in data.split(",")[:max_points]] if data else []


async def cached_sparkline(request, *args, **kwargs):
    key = ("sparkline/" + hashlib.md5(str(request.url).encode("utf-8")).hexdigest()).encode("latin1")
    ret = await mc.get(key)
    if not ret:
        ret = sparkline(*args, **kwargs)
        await mc.set(key, ret, exptime=cache_ttl)
    return ret


def sparkline(points, yticks=False, hticks_start=None, hticks_step=6, format="png"):
    fig, ax = plt.subplots(1, 1, figsize=(5, 1))
    plt.plot(points, color='b')
    plt.plot(0, points[0], color='b', marker='o')
    [v.set_visible(False) for v in ax.spines.values()]
    ax.tick_params(axis='both', which='both', length=0, labelsize="large")
    ax.set_xticks([])
    ax.set_yticks([])
    if yticks:
        max_tick = math.ceil(max(points))
        min_tick = math.floor(min(points))
        mid_tick = round((max_tick + min_tick) / 2, 1)
        ticks = [min_tick, mid_tick, max_tick]
        ax.set_yticks(ticks)
    if hticks_start:
        hticks_step = 6
        htick_positions = range(0, len(points))
        htick_labels = [(hticks_start + i) % 24 if i % hticks_step == 0 else '·' for i in htick_positions]
        ax.set_xticks(htick_positions)
        ax.set_xticklabels(htick_labels)
    ret = io.BytesIO()
    plt.savefig(ret, dpi=170, bbox_inches='tight', format=format)
    return ret.getvalue()
