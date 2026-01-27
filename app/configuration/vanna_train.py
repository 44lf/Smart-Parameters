  # 训练业务文档
class TrainData:
    documentation = """
        用户健康风险测评记录表包含NRS2002营养风险筛查的完整评分数据。
        重要字段说明：
        - total_score: 总分(0-7分)，分数越高风险越大
        - nutritional_impairment_score: 营养受损评分(0-3分)
        - disease_severity_score: 疾病严重度评分(0-3分)  
        - age_score: 年龄评分(0-1分)，70岁以上为1分
        - risk_level: 风险等级，根据总分自动计算
        - assessment_count: 测评次数，反映用户测评频率
        
        常用查询模式：
        1. 查询高风险患者（小风险，则查询低风险）：WHERE risk_level = '高风险'
        2. 按时间范围查询：WHERE assessment_time BETWEEN '开始时间' AND '结束时间'
        3. 统计各风险等级人数：GROUP BY risk_level
        4. 查询用户历史测评记录：WHERE user_id is not null
        """


    # 训练示例SQL查询
    example_sqls = [
        "SELECT user_name, age, total_score, risk_level FROM user_health_risk_assessment WHERE risk_level = '高风险' ORDER BY total_score DESC LIMIT 10",
        "SELECT risk_level, COUNT(*) as count FROM user_health_risk_assessment GROUP BY risk_level ORDER BY count DESC",
        "SELECT user_name, assessment_time, total_score FROM user_health_risk_assessment WHERE user_id = 'USER001' ORDER BY assessment_time DESC",
        "SELECT AVG(total_score) as avg_score, AVG(age) as avg_age FROM user_health_risk_assessment WHERE sex = '男'",
        "SELECT DATE(assessment_time) as date, COUNT(*) as daily_count FROM user_health_risk_assessment GROUP BY DATE(assessment_time) ORDER BY date DESC LIMIT 7"
    ]




