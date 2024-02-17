import websockets
from pymitter import EventEmitter
import json

player_event_emitter = EventEmitter()


async def player_websocket():
    while True:
        try:
            async with websockets.connect(f"ws://tracking:6002/players") as websocket:
                async for message in websocket:
                    try:
                        json_message = json.loads(message)
                        field = json_message["type"]
                        awaitable = player_event_emitter.emit_async(
                            field, json_message)
                        await awaitable
                    except:
                        pass
        except:
            continue
