<div align="center">

# Arknights Kit

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![License](https://img.shields.io/github/license/RF-Tar-Railt/arknights-kit)](https://github.com/RF-Tar-Railt/arknights-kit/blob/master/LICENSE)
[![pdm-managed](https://img.shields.io/badge/pdm-managed-blueviolet)](https://pdm.fming.dev)
[![PyPI](https://img.shields.io/pypi/v/arknights-kit)](https://img.shields.io/pypi/v/arknights-kit)

</div>

明日方舟(Arknights) 相关功能的整合库

现拥有如下功能：

- 抽卡
- 模拟十连
- 随机干员生成
- 公招链接生成

## 安装

```shell
pip install arknights-kit
```

```shell
pdm add arknights-kit
```

## 示例

```python
from arknights_kit import ArknightsGacha, GachaUser, simulate_image
from pathlib import Path
import asyncio


async def main():
    gacha = ArknightsGacha()
    user = GachaUser()
    data = gacha.gacha(user, 10)
    img = await simulate_image(data[0])
    with Path("example_sim.png").open("wb+") as f:
        f.write(img)

asyncio.run(main())
```

抽卡结果:

<img src="./example_sim.png" align="left">