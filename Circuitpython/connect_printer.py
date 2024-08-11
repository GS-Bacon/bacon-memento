import asyncio
import unicodedata
from dataclasses import dataclass
from typing import Optional

from bleak import BleakClient, BleakScanner, BLEDevice
from PIL import Image, ImageDraw, ImageFont

# DEVICE_NAME = 'M02'
address = "11:12:66:FF:15:CA"
CONNECTION_RETRY_MAX_COUNT = 3
ESC = b"\x1b"
CHARACTERISTIC_UUID_WRITE = "0000ff02-0000-1000-8000-00805f9b34fb"
GS = b"\x1d"
# 1 line = 576 dots = 72 bytes x 8 bit
DOT_PER_LINE = 576
BYTE_PER_LINE = DOT_PER_LINE // 8


@dataclass
class BitmapData:
    bitmap: bytes
    width: int
    height: int


async def main():
    # scan and connect
    text = ""
    device = await connect()
    if device:
        print("connected.")
    else:
        print("device not found.")
        return
    await create_todo(device=device)


async def create_todo(device):
    todo_list: list[str] = []
    input_text = ""
    print("文字入力")
    while True:
        input_text = input("")
        if input_text == "":
            break
        todo_list.append("□ " + input_text)
    async with BleakClient(device) as client:
        await init_printer(client=client)
        for itext in todo_list:
            text = get_east_asian_width_count(text=itext, max=32)
            for t in text:
                await print_text(client=client, text=t, fontsize=20)
            # 印字データ書き込みのあとにすぐDisconnectしてしまうとうまく動かないので少し待つ
        await feed(client=client, line=4)
        await asyncio.sleep(2)


async def connect() -> Optional[BLEDevice]:
    retry_count = 0
    device = None
    while not device and retry_count < CONNECTION_RETRY_MAX_COUNT:
        device = await BleakScanner.find_device_by_address(device_identifier=address)
        retry_count += 1
    return device


async def init_printer(client: BleakClient):
    print(f"init printer")
    await send_command(client=client, data=ESC + b"@" + b"\x1f\x11\x02\x04")


async def send_command(client: BleakClient, data: bytes):
    await client.write_gatt_char(
        char_specifier=CHARACTERISTIC_UUID_WRITE, data=data, response=True
    )


async def feed(client: BleakClient, line: int = 1):
    print(f"feed paper: {line} lines")
    await send_command(client=client, data=ESC + b"d" + line.to_bytes(1, "little"))


async def print_line(client: BleakClient):
    # GS v 0 コマンド
    # パラメータの詳細はESC/POSのコマンドリファレンスを参照
    # ビットマップのx,yサイズはリトルエンディアンで送信する必要があるので注意
    command = (
        GS
        + b"v0"
        + int(0).to_bytes(1, byteorder="little")
        + int(BYTE_PER_LINE).to_bytes(2, byteorder="little")
        + int(1).to_bytes(2, byteorder="little")
    )
    await send_command(client=client, data=command)

    # 上記コマンドで指定したバイト数分のビットマップデータを送信する
    line_data = bytearray([0xFF] * BYTE_PER_LINE)
    await send_command(client=client, data=line_data)


async def print_text(client: BleakClient, text: str, fontsize: int = 24):
    # 指定した文字が描かれたビットマップを生成して取得
    bitmap_data = text_to_bitmap(text=text, fontsize=fontsize)

    # GS v 0 コマンド
    command = (
        GS
        + b"v0"
        + int(0).to_bytes(1, byteorder="little")
        + int(BYTE_PER_LINE).to_bytes(2, byteorder="little")
        + int(bitmap_data.height).to_bytes(2, byteorder="little")
    )
    await send_command(client=client, data=command)

    # 上記コマンドで指定したバイト数分のビットマップデータを送信する
    await send_command(client=client, data=bitmap_data.bitmap)


def text_to_bitmap(text: str, fontsize: int) -> BitmapData:
    # 必要なビットマップサイズ
    font = ImageFont.truetype("C:/Windows/Fonts/YuGothL.ttc", fontsize)
    image_width = DOT_PER_LINE
    image_height = int(fontsize * 1.5)

    # ビットマップを作成
    img = Image.new("1", (image_width, image_height), 0)
    draw = ImageDraw.Draw(img)

    # 文字を描画する
    draw.text((0, 0), text, font=font, fill=1)

    # ビットマップのバイト列を返却する
    return BitmapData(img.tobytes(), image_width, image_height)


def get_east_asian_width_count(text, max: int):
    count = 0
    result: list[str] = []
    baind_text: str = ""
    flag: bool = False
    for c in text:
        if unicodedata.east_asian_width(c) in "FWA":
            count += 2
        else:
            count += 1
        baind_text += c
        if count > max - 2:
            result.append(baind_text)
            baind_text = ""
            count = 0
            flag = True
    if flag == False:
        result.append(text)
    return result


if __name__ == "__main__":
    asyncio.run(main())
