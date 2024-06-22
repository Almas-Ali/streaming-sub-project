import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaPlayer
import aiohttp


async def run(pc):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:8080/offer",
            json={"sdp": pc.localDescription.sdp, "type": pc.localDescription.type},
        ) as resp:
            response = await resp.json()
            await pc.setRemoteDescription(
                RTCSessionDescription(sdp=response["sdp"], type=response["type"])
            )


async def main():
    pc = RTCPeerConnection()

    player = MediaPlayer(
        "/dev/video0",
        format="v4l2",
        options={"framerate": "30", "video_size": "640x480"},
    )
    video_track = player.video

    @pc.on("datachannel")
    def on_datachannel(channel):
        @channel.on("message")
        def on_message(message):
            print("Data channel message:", message)

    @pc.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange():
        if pc.iceConnectionState == "failed":
            await pc.close()

    @pc.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange():
        if pc.iceConnectionState in ["failed", "disconnected", "closed"]:
            await pc.close()

    pc.addTrack(video_track)

    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)

    await run(pc)

    # Keep the script running
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
