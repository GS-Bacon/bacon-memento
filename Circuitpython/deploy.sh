#!/bin/sh

set -e
set -x

# Adafruit CircuitPython Libraries の配布URL
ADAFRUIT_LIB_BUNDLE_URL="https://github.com/adafruit/Adafruit_CircuitPython_Bundle/releases/download/20240730/adafruit-circuitpython-bundle-9.x-mpy-20240730.zip"

# Adafruit CircuitPython Librraries を展開したディレクトリ
#   - このスクリプトと同じディレクトリに展開している場合は以下のままでOK
ADAFRUIT_LIB_BUNDLE_PATH="./adafruit-circuitpython-bundle-9.x-mpy-20240730"

# デプロイ先
#   - macOSならこのままでOK
#   - それ以外のOSは適宜変更
DST="/Volumes/CIRCUITPY"

# ライブラリのデプロイ先
LIBDST="${DST}/lib"

# adafruit-circuitpython-bundle-9.x-mpy-20240730 がなければダウンロードして展開
if [ ! -d "${ADAFRUIT_LIB_BUNDLE_PATH}" ]; then
  curl -L -O "${ADAFRUIT_LIB_BUNDLE_URL}"
  unzip adafruit-circuitpython-bundle-9.x-mpy-20240730.zip
fi

rm -rf "${DST}"/code.py
rm -rf "${LIBDST}"
mkdir -p "${LIBDST}"

# 外部ライブラリをコピー
cp "${ADAFRUIT_LIB_BUNDLE_PATH}"/lib/adafruit_aw9523.mpy "${LIBDST}"
cp "${ADAFRUIT_LIB_BUNDLE_PATH}"/lib/adafruit_lis3dh.mpy "${LIBDST}"
cp "${ADAFRUIT_LIB_BUNDLE_PATH}"/lib/neopixel.mpy "${LIBDST}"
cp "${ADAFRUIT_LIB_BUNDLE_PATH}"/lib/adafruit_debouncer.mpy "${LIBDST}"
cp "${ADAFRUIT_LIB_BUNDLE_PATH}"/lib/adafruit_ticks.mpy "${LIBDST}"
cp -r "${ADAFRUIT_LIB_BUNDLE_PATH}"/lib/adafruit_register "${LIBDST}"
cp -r "${ADAFRUIT_LIB_BUNDLE_PATH}"/lib/adafruit_display_text "${LIBDST}"
cp -r "${ADAFRUIT_LIB_BUNDLE_PATH}"/lib/adafruit_ov5640 "${LIBDST}"

# 自作ライブラリをコピー
cp -r ./lib/* "${LIBDST}"

# メインコードをコピー
cp -r ./main.py "${DST}"/main.py
