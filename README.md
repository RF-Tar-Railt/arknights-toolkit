<div align="center">

# Arknights-Toolkit

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![License](https://img.shields.io/github/license/RF-Tar-Railt/arknights-toolkit)](https://github.com/RF-Tar-Railt/arknights-toolkit/blob/master/LICENSE)
[![pdm-managed](https://img.shields.io/badge/pdm-managed-blueviolet)](https://pdm.fming.dev)
[![PyPI](https://img.shields.io/pypi/v/arknights-toolkit)](https://img.shields.io/pypi/v/arknights-toolkit)

</div>

明日方舟(Arknights) 相关功能的整合库

现拥有如下功能：

- 抽卡
- 模拟十连
- 随机干员生成
- 公招链接生成
- 猜干员游戏
- 抽卡结果查询

**欢迎 PR**

## 安装

```shell
pip install arknights-toolkit
```

```shell
pdm add arknights-toolkit
```

## 配置

`arknights-toolkit` 配套了 cli 工具用于资源下载:

初始化数据与图片资源:
```shell
arkkit init
```

更新抽卡卡池:
```shell
arkkit update gacha path/to/gacha.json
```

## 示例

```python
from arknights_toolkit.gacha import ArknightsGacha, GachaUser
from arknights_toolkit.gacha.simulate import simulate_image
from pathlib import Path
import asyncio


async def main():
    gacha = ArknightsGacha("path/to/gacha.json")
    user = GachaUser()
    data = gacha.gacha(user, 10)
    img = await simulate_image(data[0])
    with Path("example_sim.png").open("wb+") as f:
        f.write(img)

asyncio.run(main())
```

抽卡结果:

<img src="https://github.com/RF-Tar-Railt/arknights-toolkit/blob/master/example_sim.png" align="left" width="640" height="360" alt="抽卡结果">