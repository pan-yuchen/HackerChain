#!/usr/bin/env python3
"""
小红书 MCP 客户端
通过 HTTP/SSE 传输连接到小红书 MCP 服务器
"""

import requests
import json
import os
from typing import Dict, Any, Optional, List


class XiaohongshuMCPClient:
    def __init__(self, base_url: str = "http://localhost:18060/mcp"):
        """
        初始化小红书 MCP 客户端
        
        Args:
            base_url: MCP 服务器的 URL
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.message_id = 0
        self.initialized = False
        self.session_id = None
    
    def _get_next_id(self) -> int:
        """获取下一个消息 ID"""
        self.message_id += 1
        return self.message_id
    
    def _send_message(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        发送 JSON-RPC 消息
        
        Args:
            method: JSON-RPC 方法名
            params: 方法参数
        
        Returns:
            响应结果
        """
        message = {
            "jsonrpc": "2.0",
            "method": method,
            "id": self._get_next_id()
        }
        
        if params is not None:
            message["params"] = params
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        
        # 添加 session ID（如果存在）
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        
        response = self.session.post(
            self.base_url,
            json=message,
            headers=headers,
            stream=True
        )
        
        # 保存 session ID
        if 'Mcp-Session-Id' in response.headers:
            self.session_id = response.headers['Mcp-Session-Id']
        
        response.raise_for_status()
        
        # 解析响应（可能是 JSON 或 SSE 格式）
        content_type = response.headers.get('Content-Type', '')
        
        if 'application/json' in content_type:
            # 直接返回 JSON
            return response.json()
        else:
            # 解析 SSE 流
            for line in response.iter_lines():
                if not line:
                    continue
                
                line = line.decode('utf-8')
                
                if line.startswith('data: '):
                    data = line[6:]
                    try:
                        result = json.loads(data)
                        if 'result' in result or 'error' in result:
                            return result
                    except json.JSONDecodeError:
                        continue
        
        return {}
    
    def _send_notification(self, method: str, params: Optional[Dict[str, Any]] = None) -> None:
        """
        发送通知（不需要响应）
        
        Args:
            method: 通知方法名
            params: 通知参数
        """
        message = {
            "jsonrpc": "2.0",
            "method": method
        }
        
        if params is not None:
            message["params"] = params
        
        headers = {"Content-Type": "application/json"}
        
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        
        response = self.session.post(
            self.base_url,
            json=message,
            headers=headers
        )
        response.raise_for_status()
    
    def initialize(self) -> Dict[str, Any]:
        """初始化 MCP 连接"""
        result = self._send_message("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "roots": {"listChanged": True},
                "sampling": {}
            },
            "clientInfo": {
                "name": "xiaohongshu-python-client",
                "version": "1.0.0"
            }
        })
        
        # 发送 initialized 通知完成握手
        self._send_notification("notifications/initialized")
        self.initialized = True
        
        return result
    
    def list_tools(self) -> Dict[str, Any]:
        """获取可用工具列表"""
        if not self.initialized:
            raise Exception("Client not initialized. Call initialize() first.")
        
        return self._send_message("tools/list", {})
    
    def call_tool(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        调用指定的工具
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
        
        Returns:
            工具执行结果
        """
        if not self.initialized:
            raise Exception("Client not initialized. Call initialize() first.")
        
        return self._send_message("tools/call", {
            "name": tool_name,
            "arguments": arguments or {}
        })
    
    # ==================== 便捷方法：封装小红书功能 ====================
    
    def check_login_status(self) -> Dict[str, Any]:
        """检查登录状态"""
        return self.call_tool("check_login_status")
    
    def get_login_qrcode(self) -> Dict[str, Any]:
        """获取登录二维码（返回 Base64 图片）"""
        return self.call_tool("get_login_qrcode")
    
    def list_feeds(self) -> Dict[str, Any]:
        """获取首页 Feeds 列表"""
        return self.call_tool("list_feeds")
    
    def search_feeds(self, keyword: str, filters: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        搜索小红书内容
        
        Args:
            keyword: 搜索关键词
            filters: 筛选选项，可包含：
                - sort_by: 综合|最新|最多点赞|最多评论|最多收藏
                - note_type: 不限|视频|图文
                - publish_time: 不限|一天内|一周内|半年内
                - search_scope: 不限|已看过|未看过|已关注
                - location: 不限|同城|附近
        
        Returns:
            搜索结果
        """
        args = {"keyword": keyword}
        if filters:
            args["filters"] = filters
        return self.call_tool("search_feeds", args)
    
    def get_feed_detail(self, feed_id: str, xsec_token: str) -> Dict[str, Any]:
        """
        获取笔记详情
        
        Args:
            feed_id: 笔记ID
            xsec_token: 访问令牌（从 Feed 列表获取）
        
        Returns:
            笔记详情
        """
        return self.call_tool("get_feed_detail", {
            "feed_id": feed_id,
            "xsec_token": xsec_token
        })
    
    def like_feed(self, feed_id: str, xsec_token: str, unlike: bool = False) -> Dict[str, Any]:
        """
        点赞或取消点赞笔记
        
        Args:
            feed_id: 笔记ID
            xsec_token: 访问令牌
            unlike: True=取消点赞，False=点赞
        
        Returns:
            操作结果
        """
        return self.call_tool("like_feed", {
            "feed_id": feed_id,
            "xsec_token": xsec_token,
            "unlike": unlike
        })
    
    def favorite_feed(self, feed_id: str, xsec_token: str, unfavorite: bool = False) -> Dict[str, Any]:
        """
        收藏或取消收藏笔记
        
        Args:
            feed_id: 笔记ID
            xsec_token: 访问令牌
            unfavorite: True=取消收藏，False=收藏
        
        Returns:
            操作结果
        """
        return self.call_tool("favorite_feed", {
            "feed_id": feed_id,
            "xsec_token": xsec_token,
            "unfavorite": unfavorite
        })
    
    def post_comment(self, feed_id: str, xsec_token: str, content: str) -> Dict[str, Any]:
        """
        发表评论
        
        Args:
            feed_id: 笔记ID
            xsec_token: 访问令牌
            content: 评论内容
        
        Returns:
            评论结果
        """
        return self.call_tool("post_comment_to_feed", {
            "feed_id": feed_id,
            "xsec_token": xsec_token,
            "content": content
        })
    
    def get_user_profile(self, user_id: str, xsec_token: str) -> Dict[str, Any]:
        """
        获取用户主页
        
        Args:
            user_id: 用户ID
            xsec_token: 访问令牌
        
        Returns:
            用户信息
        """
        return self.call_tool("user_profile", {
            "user_id": user_id,
            "xsec_token": xsec_token
        })
    
    def publish_content(self, title: str, content: str, images: List[str], 
                       tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        发布图文内容
        
        Args:
            title: 标题（最多20个中文字）
            content: 正文内容
            images: 图片路径列表（支持本地路径或 HTTP/HTTPS 链接）
            tags: 话题标签列表（可选）
        
        Returns:
            发布结果
        """
        # 如果 title 或 content 为空，设置为默认值 "test"
        if not title:
            title = "test"
        if not content:
            content = "test"
        
        # 如果没有提供图片，使用默认图片
        if not images:
            default_image = "/Users/panyuchen/codes/hks/output/generated_image_0.png"
            if os.path.exists(default_image):
                images = [default_image]
            else:
                # 如果默认图片不存在，保持空列表（让服务端处理错误）
                images = []
        
        args = {
            "title": title,
            "content": content,
            "images": images
        }
        if tags:
            args["tags"] = tags
        
        return self.call_tool("publish_content", args)
    
    def publish_video(self, title: str, content: str, video: str,
                     tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        发布视频内容
        
        Args:
            title: 标题（最多20个中文字）
            content: 正文内容
            video: 本地视频文件绝对路径
            tags: 话题标签列表（可选）
        
        Returns:
            发布结果
        """
        args = {
            "title": title,
            "content": content,
            "video": video
        }
        if tags:
            args["tags"] = tags
        
        return self.call_tool("publish_with_video", args)


def main():
    """示例：如何使用客户端"""
    
    client = XiaohongshuMCPClient()
    
    try:
        # 1. 初始化连接
        print("正在初始化 MCP 连接...")
        init_result = client.initialize()
        print(f"✓ 初始化成功\n")
        
        # 2. 检查登录状态
        print("正在检查登录状态...")
        login_status = client.check_login_status()
        result = login_status.get('result', {})
        if result.get('content'):
            text = result['content'][0].get('text', '')
            print(f"✓ {text}\n")
        
        # 3. 获取工具列表
        print("正在获取可用工具...")
        tools = client.list_tools()
        tools_list = tools.get('result', {}).get('tools', [])
        print(f"✓ 可用工具数量: {len(tools_list)}")
        for tool in tools_list:
            print(f"  - {tool['name']}: {tool.get('description', '')}")
        print()
        
        # 4. 搜索内容示例
        print("正在搜索内容: '美食'...")
        search_result = client.search_feeds(keyword="美食")
        print(f"✓ 搜索完成\n")
        
        # 5. 获取首页 Feeds
        print("正在获取首页 Feeds...")
        feeds = client.list_feeds()
        print(f"✓ 获取成功\n")
        
    except requests.exceptions.RequestException as e:
        print(f"✗ 请求错误: {e}")
    except Exception as e:
        print(f"✗ 发生错误: {e}")


if __name__ == "__main__":
    main()