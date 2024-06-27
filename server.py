import asyncio
import json
import random
import time
from typing import Set

from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.rtcdatachannel import RTCDataChannel

# from aiortc.contrib.media import MediaRecorder, MediaStreamTrack

pcs: Set[RTCPeerConnection] = set()


def get_random_id() -> int:
    return random.randint(1, 1000)


async def offer(request: web.Request) -> web.Response:
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pcs.add(pc)

    fp = open(f"received_video_{get_random_id()}.mp4", "wb")

    @pc.on("datachannel") # type: ignore
    def on_datachannel(channel: RTCDataChannel) -> None: # type: ignore
        start = time.time()
        octets = 0

        @channel.on("message") # type: ignore
        async def on_message(message: bytes) -> None: # type: ignore
            nonlocal octets

            if message:
                octets += len(message)
                fp.write(message)
            else:
                elapsed = time.time() - start
                print(
                    "received %d bytes in %.1f s (%.3f Mbps)"
                    % (octets, elapsed, octets * 8 / elapsed / 1000000)
                )

    @pc.on("iceconnectionstatechange") # type: ignore
    async def on_iceconnectionstatechange(): # type: ignore
        print("ICE connection state: ", pc.iceConnectionState)
        if pc.iceConnectionState == "failed":
            await pc.close()
            pcs.discard(pc)
            print(f"pc '{pc}' closed")

    # Receive track from client
    # @pc.on("track")
    # async def on_track(track: MediaStreamTrack):
    #     print("Track %s received" % track.kind)
    #     if track.kind == "video":
    #         # recorder = MediaRecorder(f"received_video_{get_random_id()}.mp4")
    #         recorder.addTrack(track)
    #         await recorder.start()

    #     # @track.on("ended")
    #     # async def on_ended():
    #     #     print("Track %s ended" % track.kind)
    #     #     await recorder.stop()

    #     @track.on("mute")
    #     async def on_mute():
    #         print("Track muted")

    #     @track.on("unmute")
    #     async def on_unmute():
    #         print("Track unmuted")

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer) # type: ignore

    return web.Response(
        content_type="application/json",
        text=json.dumps(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        ),
    )


async def on_shutdown(app: web.Application):
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()


if __name__ == "__main__":
    app = web.Application()
    app.on_shutdown.append(on_shutdown)
    app.router.add_post("/offer", offer)
    web.run_app(app, port=8080) # type: ignore
