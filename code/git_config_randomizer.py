#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git配置随机修改器
功能：随机修改git config的用户名和email，支持恢复原始配置
"""

import subprocess
import random
import string


class GitConfigRandomizer:
    def __init__(self):
        # 固定的原始配置，无论运行多少次都不会改变
        self.original_config = {
            "username": "zduu",
            "email": "mail@edxx.de"
        }
        
    def run_git_command(self, command):
        """执行git命令并返回结果"""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                print(f"命令执行失败: {command}")
                print(f"错误信息: {result.stderr}")
                return None
        except Exception as e:
            print(f"执行命令时出错: {e}")
            return None
    
    def get_current_config(self):
        """显示当前的git配置（仅用于显示，不影响原始配置）"""
        print("正在获取当前git配置...")

        # 获取用户名
        username = self.run_git_command("git config --global user.name")
        if username is None:
            username = ""

        # 获取邮箱
        email = self.run_git_command("git config --global user.email")
        if email is None:
            email = ""

        print(f"当前配置:")
        print(f"  用户名: {username if username else '未设置'}")
        print(f"  邮箱: {email if email else '未设置'}")

        print(f"\n固定的原始配置（恢复时使用）:")
        print(f"  用户名: {self.original_config['username']}")
        print(f"  邮箱: {self.original_config['email']}")

        return self.original_config
    

    
    def generate_random_username(self):
        """生成随机用户名"""
        # 随机选择用户名风格
        styles = [
            # 风格1: 形容词 + 名词
            lambda: f"{random.choice(['Cool', 'Smart', 'Fast', 'Bright', 'Quick', 'Sharp', 'Bold', 'Wild', 'Free', 'Pure'])}{random.choice(['Coder', 'Dev', 'Hacker', 'Ninja', 'Master', 'Guru', 'Pro', 'Expert', 'Wizard', 'Hero'])}",
            
            # 风格2: 动物 + 数字
            lambda: f"{random.choice(['Tiger', 'Eagle', 'Wolf', 'Fox', 'Lion', 'Bear', 'Shark', 'Falcon', 'Panther', 'Dragon'])}{random.randint(100, 999)}",
            
            # 风格3: 随机字母 + 数字组合
            lambda: f"{''.join(random.choices(string.ascii_lowercase, k=random.randint(5, 8)))}{random.randint(10, 99)}",
            
            # 风格4: 技术相关词汇
            lambda: f"{random.choice(['Code', 'Git', 'Dev', 'Tech', 'Byte', 'Bit', 'Data', 'Logic', 'Algo', 'Script'])}{random.choice(['Master', 'King', 'Lord', 'Boss', 'Chief', 'Star', 'Pro', 'Ace', 'Top', 'Max'])}"
        ]
        
        return random.choice(styles)()
    
    def generate_random_email(self):
        """生成随机邮箱"""
        # 邮箱前缀
        prefix_styles = [
            # 风格1: 随机字母
            lambda: ''.join(random.choices(string.ascii_lowercase, k=random.randint(6, 10))),
            
            # 风格2: 字母 + 数字
            lambda: ''.join(random.choices(string.ascii_lowercase, k=random.randint(4, 6))) + str(random.randint(100, 9999)),
            
            # 风格3: 单词组合
            lambda: f"{random.choice(['test', 'demo', 'user', 'dev', 'code', 'temp'])}{random.randint(10, 999)}"
        ]
        
        # 邮箱域名
        domains = [
            'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 
            'example.com', 'test.com', 'demo.org', 'temp.net',
            'protonmail.com', '163.com', 'qq.com'
        ]
        
        prefix = random.choice(prefix_styles)()
        domain = random.choice(domains)
        
        return f"{prefix}@{domain}"
    
    def set_random_config(self):
        """设置随机的git配置"""
        print("\n正在生成随机配置...")
        
        # 生成随机用户名和邮箱
        new_username = self.generate_random_username()
        new_email = self.generate_random_email()
        
        print(f"新的随机配置:")
        print(f"  用户名: {new_username}")
        print(f"  邮箱: {new_email}")
        
        # 设置新配置
        print("\n正在应用新配置...")
        
        username_result = self.run_git_command(f'git config --global user.name "{new_username}"')
        email_result = self.run_git_command(f'git config --global user.email "{new_email}"')
        
        if username_result is not None and email_result is not None:
            print("✅ 配置修改成功!")
            
            # 验证新配置
            print("\n验证新配置:")
            current_username = self.run_git_command("git config --global user.name")
            current_email = self.run_git_command("git config --global user.email")
            print(f"  当前用户名: {current_username}")
            print(f"  当前邮箱: {current_email}")
            
            return True
        else:
            print("❌ 配置修改失败!")
            return False
    
    def restore_original_config(self):
        """恢复固定的原始配置"""
        print("\n正在恢复固定的原始配置...")
        print(f"恢复到: {self.original_config['username']} <{self.original_config['email']}>")

        # 原始配置是固定的，不需要从文件读取

        # 恢复固定的用户名和邮箱
        self.run_git_command(f'git config --global user.name "{self.original_config["username"]}"')
        self.run_git_command(f'git config --global user.email "{self.original_config["email"]}"')

        print("✅ 固定的原始配置已恢复!")

        # 验证恢复结果
        print("\n验证恢复结果:")
        current_username = self.run_git_command("git config --global user.name")
        current_email = self.run_git_command("git config --global user.email")
        print(f"  当前用户名: {current_username if current_username else '未设置'}")
        print(f"  当前邮箱: {current_email if current_email else '未设置'}")

        return True
    
    def run(self):
        """主运行函数"""
        print("=" * 50)
        print("Git配置随机修改器")
        print("固定原始配置: zduu <mail@edxx.de>")
        print("=" * 50)
        
        # 显示当前配置和固定的原始配置
        self.get_current_config()
        
        # 设置随机配置
        if self.set_random_config():
            # 询问是否恢复
            print("\n" + "=" * 50)
            while True:
                choice = input("是否要恢复原始配置? (y/n): ").lower().strip()
                if choice in ['y', 'yes', '是', 'Y']:
                    self.restore_original_config()
                    break
                elif choice in ['n', 'no', '否', 'N']:
                    print("保持当前随机配置。")
                    print("如需恢复到固定原始配置，请重新运行此脚本并选择恢复选项。")
                    break
                else:
                    print("请输入 y(是) 或 n(否)")
        
        print("\n程序结束。")


def main():
    """主函数"""
    randomizer = GitConfigRandomizer()
    randomizer.run()


if __name__ == "__main__":
    main()
