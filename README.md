# 四川家庭 IPTV

面向**成都移动家庭网络**的个人可维护 IPTV 播放列表。目标是为家中电视提供一个固定订阅地址，重点整理央视、主流卫视、四川省级、成都及四川地方公开频道。

> 当前处于首轮搭建阶段。播放列表尚未完成成都移动网络实测，`output/parents-test.m3u` 用于测试，`output/parents.m3u` 仅收录确认过的稳定线路。

## 电视订阅地址

- 首轮测试版：`https://raw.githubusercontent.com/JIDAIN/sichuan-iptv/main/output/parents-test.m3u`
- 家庭稳定版：`https://raw.githubusercontent.com/JIDAIN/sichuan-iptv/main/output/parents.m3u`

## 设计原则

- 电视端始终使用固定地址，维护时无需重新安装应用。
- 成都移动家庭实测优先于 GitHub 云端检测结果。
- 一次检测失败不会删除已经验证的线路。
- 重要频道可保留多条不同来源的备用线路。
- 自动任务失败时不覆盖上一份稳定播放列表。
- 不收录需要盗用账号、Cookie、Token 或绕过付费鉴权的线路。

## 目录

```text
config/
  channels.csv       想要的频道、分组、排序及别名
  sources.txt        公开候选播放列表来源
  verified.csv       成都移动家庭实测结果
scripts/
  build_playlist.py  汇总、规范化、去重并生成播放列表
output/
  parents-test.m3u   待家庭实测的候选版
  parents.m3u        已确认的家庭稳定版
  report.md          本次构建报告
.github/workflows/
  update.yml         定时构建及保守更新
```

## 工作流程

1. GitHub Actions 定时读取 `config/sources.txt` 中的公开来源。
2. 按 `config/channels.csv` 统一名称、分组与顺序。
3. 生成候选测试版，不自动覆盖家庭稳定版。
4. 在成都移动宽带下通过电视实测。
5. 将实测结果记录到 `config/verified.csv`，再生成正式版。

## 合规说明

本仓库只用于整理用户有权访问的公开直播地址，不存储或转播视频内容。频道版权归相应权利人所有；如上游地址不再公开或权利人要求移除，应及时删除。
