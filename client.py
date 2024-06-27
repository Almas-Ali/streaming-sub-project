import asyncio

import aiohttp
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCDataChannel

# from aiortc.contrib.media import MediaPlayer


async def run(pc: RTCPeerConnection):
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

    # For video stream with webcam
    # player = MediaPlayer(
    #     "/dev/video0",
    #     # "video.mp4",
    #     format="v4l2",
    #     # format="video4linux2",
    #     # options={"framerate": "30", "video_size": "640x480"},
    #     options={"framerate": "30", "video_size": "1280x720"},
    # )

    # For send video file as track
    # player = MediaPlayer("video.mp4")
    # video_track = player.video

    fp = open("video.mp4", "rb")

    done_reading: bool = False
    channel: RTCDataChannel = pc.createDataChannel("video_stream") # type: ignore

    def send_data() -> None:
        nonlocal done_reading

        while (
            channel.bufferedAmount <= channel.bufferedAmountLowThreshold
        ) and not done_reading:
            data = fp.read(16384)
            channel.send(data)
            if not data:
                done_reading = True

    channel.on("bufferedamountlow", send_data)
    channel.on("open", send_data)

    @pc.on("iceconnectionstatechange") # type: ignore
    async def on_iceconnectionstatechange(): # type: ignore
        if pc.iceConnectionState in ["failed", "disconnected", "closed"]:
            await pc.close()

    # send track
    # pc.addTrack(video_track)

    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)

    await run(pc)

    # Keep the script running
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
