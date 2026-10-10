# 工作区原则

## 图片读取（强制）

会话模型多数**不支持直接看图**（附件会被省略），但本机已装好读图工具。凡用户消息里出现图片/截图，附件一定是这种形式：

```
[Attached image/png: image.png]
[Media omitted from provider request because the selected model does not support image input.]
[Image: source: C:\Users\123\.zcode\cli\image-cache\<会话ID>\image-<hash>.png]
```

**必须按以下流程处理（不得跳过）：**

1. 从 `[Image: source: ...]` 行取出**图片的绝对路径**（这就是文件位置）；
2. **立即调用读图工具**（picturereader 插件提供，工具名以 `image_scan` / `image_ocr` / `image_sample` 结尾，可能带 `mcp__` 前缀）：
   - `image_scan(file_path, size?)`：第一轮全局扫描——色相分布（hue families）、结构（对称/条带）、区域色块；
   - 需要读图中文字（界面截图必做）→ `image_ocr(file_path)`；
   - 需要判颜色/材质/纹理 → `image_sample(file_path, region)`；
3. **禁止**回复「当前模型不支持图片输入 / 无法查看图片 / 请把图里的文字发给我」——**先调用上述工具**，确实读不出内容再如实说明；
4. 若工具列表中找不到上述工具（说明本会话未启用 picturereader 插件）：明确告知用户到「设置 → 插件」用**工作区**作用域启用 picturereader 后**新建会话**，再继续。
