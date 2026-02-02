import random
import time

class NumberGuessingGame:
    """
    猜数字游戏
    玩家需要猜出1-100之间的随机数字cd app/test
python hello.pycd app/test
python hello.py
    """

    def __init__(self):
        self.min_number = 1
        self.max_number = 100
        self.secret_number = None
        self.attempts = 0
        self.best_score = float('inf')

    def generate_secret_number(self):
        """生成秘密数字"""
        self.secret_number = random.randint(self.min_number, self.max_number)
        self.attempts = 0

    def get_hint(self, guess):
        """根据猜测给出提示"""
        if guess < self.secret_number:
            return "太小了！试试更大的数字。"
        elif guess > self.secret_number:
            return "太大了！试试更小的数字。"
        else:
            return "恭喜你猜对了！"

    def play_round(self):
        """玩一轮游戏"""
        print("\n" + "="*50)
        print("欢迎来到猜数字游戏！")
        print(f"我已经想好了一个 {self.min_number} 到 {self.max_number} 之间的数字。")
        print("看看你能用多少次猜中它！")
        print("="*50)

        self.generate_secret_number()

        while True:
            try:
                guess_input = input(f"\n请输入你的猜测 ({self.min_number}-{self.max_number}): ")
                guess = int(guess_input)

                if guess < self.min_number or guess > self.max_number:
                    print(f"请输入 {self.min_number} 到 {self.max_number} 之间的数字！")
                    continue

                self.attempts += 1

                hint = self.get_hint(guess)
                print(f"第 {self.attempts} 次尝试: {hint}")

                if guess == self.secret_number:
                    print(f"\n🎉 太棒了！你用了 {self.attempts} 次猜中了数字 {self.secret_number}！")

                    if self.attempts < self.best_score:
                        self.best_score = self.attempts
                        print(f"🏆 新的最佳记录：{self.best_score} 次！")
                    elif self.best_score != float('inf'):
                        print(f"当前最佳记录：{self.best_score} 次")

                    break

            except ValueError:
                print("请输入有效的数字！")

    def show_menu(self):
        """显示游戏菜单"""
        while True:
            print("\n" + "="*50)
            print("猜数字游戏菜单")
            print("="*50)
            print("1. 开始新游戏")
            print("2. 查看游戏规则")
            print("3. 查看最佳记录")
            print("4. 退出游戏")
            print("="*50)

            choice = input("请选择 (1-4): ")

            if choice == "1":
                self.play_round()
            elif choice == "2":
                self.show_rules()
            elif choice == "3":
                self.show_best_score()
            elif choice == "4":
                print("\n谢谢游玩！再见！👋")
                break
            else:
                print("无效的选择，请重新输入！")

    def show_rules(self):
        """显示游戏规则"""
        print("\n" + "="*50)
        print("游戏规则")
        print("="*50)
        print("1. 计算机会随机生成一个 1-100 之间的数字")
        print("2. 你需要猜出这个数字是多少")
        print("3. 每次猜测后，计算机会告诉你：")
        print("   - '太小了'：如果你的猜测比秘密数字小")
        print("   - '太大了'：如果你的猜测比秘密数字大")
        print("   - '猜对了'：如果你的猜测正确")
        print("4. 目标是用最少的次数猜中数字")
        print("5. 每次游戏结束后会更新最佳记录")
        print("="*50)

    def show_best_score(self):
        """显示最佳记录"""
        print("\n" + "="*50)
        print("最佳记录")
        print("="*50)
        if self.best_score == float('inf'):
            print("还没有最佳记录，快来玩一局吧！")
        else:
            print(f"最佳记录：{self.best_score} 次")
        print("="*50)


def main():
    """游戏主函数"""
    print("正在启动猜数字游戏...")
    time.sleep(1)

    game = NumberGuessingGame()
    game.show_menu()


if __name__ == "__main__":
    main()