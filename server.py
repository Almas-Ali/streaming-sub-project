import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRecorder, MediaStreamTrack
from aiohttp import web
import json

pcs: set[RTCPeerConnection] = set()


async def offer(request: web.Request) -> web.Response:
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange():
        print("ICE connection state: ", pc.iceConnectionState)
        if pc.iceConnectionState == "failed":
            await pc.close()
            pcs.discard(pc)
            print(f"pc '{pc}' closed")

    @pc.on("track")
    async def on_track(track: MediaStreamTrack):
        print("Track %s received" % track.kind)
        if track.kind == "video":
            recorder = MediaRecorder("received_video.mp4")
            recorder.addTrack(track)
            await recorder.start()

        @track.on("ended")
        async def on_ended():
            print("Track %s ended" % track.kind)
            await recorder.stop()

        @track.on("mute")
        async def on_mute():
            print("Track muted")

        @track.on("unmute")
        async def on_unmute():
            print("Track unmuted")

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

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
    web.run_app(app, port=8080)
