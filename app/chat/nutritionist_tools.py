import logging
from langchain.tools import BaseTool, tool
from typing import List

logger = logging.getLogger("nutritionist_tools")


class NutritionistTools:
    """营养师工具集"""

    @staticmethod
    def get_tools() -> List[BaseTool]:
        """获取所有工具"""
        return [
            NutritionistTools.calculate_bmi,
            NutritionistTools.daily_calorie_needs,
            NutritionistTools.food_recommendation,
            NutritionistTools.nrs2002_assessment
        ]

    @tool
    def calculate_bmi(input_str: str) -> str:
        """计算BMI指数。输入格式：'体重kg,身高cm'，例如：'70,175'"""
        try:
            parts = input_str.split(',')
            if len(parts) != 2:
                return "请输入正确的格式：体重(kg),身高(cm)，例如：70,175"

            weight_kg = float(parts[0].strip())
            height_cm = float(parts[1].strip())
            height_m = height_cm / 100
            bmi = weight_kg / (height_m ** 2)

            # BMI分类
            if bmi < 18.5:
                category = "体重过轻"
            elif bmi < 24:
                category = "正常体重"
            elif bmi < 28:
                category = "超重"
            else:
                category = "肥胖"

            return f"您的BMI指数为: {bmi:.1f} ({category})"
        except Exception as e:
            return f"计算BMI时出错: {str(e)}，请确保输入正确的数字格式"

    @tool
    def daily_calorie_needs(input_str: str) -> str:
        """计算每日热量需求。输入格式：'体重kg,身高cm,年龄,性别,活动水平'，例如：'60,170,30,女,中等'"""
        try:
            parts = input_str.split(',')
            if len(parts) != 5:
                return "请输入正确的格式：体重(kg),身高(cm),年龄,性别(男/女),活动水平(低/中等/高)"

            weight_kg = float(parts[0].strip())
            height_cm = float(parts[1].strip())
            age = int(parts[2].strip())
            gender = parts[3].strip()
            activity_level = parts[4].strip()

            # 基础代谢率 (BMR)
            if gender.lower() == '男':
                bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
            else:
                bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

            # 活动系数
            activity_factors = {
                '低': 1.2,
                '中等': 1.55,
                '高': 1.725
            }

            activity_factor = activity_factors.get(activity_level, 1.2)
            daily_calories = bmr * activity_factor

            return f"您的每日热量需求约为: {daily_calories:.0f} 大卡"
        except Exception as e:
            return f"计算热量需求时出错: {str(e)}"

    @tool
    def food_recommendation(input_str: str) -> str:
        """根据健康状况和目标提供饮食建议。输入格式：'健康状况,目标'，例如：'无特殊疾病,均衡营养'"""
        try:
            parts = input_str.split(',')
            if len(parts) != 2:
                return "请输入正确的格式：健康状况,目标"

            health_condition = parts[0].strip()
            goal = parts[1].strip()

            # 简单的饮食建议逻辑
            recommendations = {
                '均衡营养': "建议饮食包含：全谷物、瘦肉蛋白、健康脂肪、大量蔬菜水果",
                '减重': "建议：控制总热量，增加蔬菜摄入，减少精制碳水",
                '增肌': "建议：增加蛋白质摄入，适量碳水，规律力量训练",
                '控制血糖': "建议：低GI食物，均衡餐次，控制碳水总量"
            }

            base_recommendation = recommendations.get(goal, "保持均衡饮食，多样化食物选择")
            return f"根据您的目标'{goal}'，{base_recommendation}"
        except Exception as e:
            return f"生成饮食建议时出错: {str(e)}"

    @tool
    def nrs2002_assessment(input_str: str) -> str:
        """NRS2002营养风险评估。输入格式：'BMI,体重下降%,疾病严重程度,年龄'，例如：'22,5,无,45'"""
        try:
            parts = input_str.split(',')
            if len(parts) != 4:
                return "请输入正确的格式：BMI,体重下降%,疾病严重程度,年龄"

            bmi = float(parts[0].strip())
            weight_loss = float(parts[1].strip())
            disease_severity = parts[2].strip()
            age = int(parts[3].strip())

            score = 0

            # BMI评分
            if bmi < 18.5:
                score += 3
            elif bmi < 20:
                score += 1

            # 体重下降评分
            if weight_loss > 10:
                score += 3
            elif weight_loss > 5:
                score += 2
            elif weight_loss > 0:
                score += 1

            # 疾病严重程度
            if disease_severity in ['严重', '高']:
                score += 3
            elif disease_severity in ['中等']:
                score += 2
            elif disease_severity in ['轻度']:
                score += 1

            # 年龄评分
            if age >= 70:
                score += 1

            # 风险评估
            if score >= 3:
                risk = "高风险"
                recommendation = "建议进行营养干预"
            else:
                risk = "低风险"
                recommendation = "建议定期监测"

            return f"NRS2002评分: {score}分，营养风险: {risk}。{recommendation}"
        except Exception as e:
            return f"营养风险评估时出错: {str(e)}"