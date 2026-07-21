# Pre-generated question bank for Aptitude Practice and Aptitude Tests

PREDEFINED_PRACTICE_QUESTIONS = {
    "Number System": [
        {
            "question": "What is the sum of the first 15 natural numbers?",
            "options": ["105", "120", "135", "150"],
            "correct_answer": "120",
            "step_by_step_solution": "Use the formula Sum = n(n+1)/2. Here n = 15. Sum = 15 * 16 / 2 = 120.",
            "tips_and_tricks": "Always use n(n+1)/2 for consecutive natural number sum.",
            "difficulty": "easy"
        },
        {
            "question": "Which of the following numbers is divisible by 9?",
            "options": ["2437", "4329", "5123", "6112"],
            "correct_answer": "4329",
            "step_by_step_solution": "Sum of digits of 4329 = 4+3+2+9 = 18. Since 18 is divisible by 9, 4329 is divisible by 9.",
            "tips_and_tricks": "Sum the digits to quickly test for 3 and 9 divisibility.",
            "difficulty": "medium"
        }
    ],
    "HCF & LCM": [
        {
            "question": "Find the HCF of 24 and 36.",
            "options": ["6", "12", "18", "24"],
            "correct_answer": "12",
            "step_by_step_solution": "Factors of 24 = 1,2,3,4,6,8,12,24. Factors of 36 = 1,2,3,4,6,9,12,18,36. Highest common factor is 12.",
            "tips_and_tricks": "The HCF is the largest difference between factors.",
            "difficulty": "easy"
        },
        {
            "question": "Two bells ring at intervals of 12 seconds and 18 seconds. If they ring together now, after how many seconds will they ring together next?",
            "options": ["24", "36", "48", "72"],
            "correct_answer": "36",
            "step_by_step_solution": "Find LCM of 12 and 18. 12 = 2^2 * 3, 18 = 2 * 3^2. LCM = 2^2 * 3^2 = 36 seconds.",
            "tips_and_tricks": "Interval problems always require LCM.",
            "difficulty": "medium"
        }
    ],
    "Percentage": [
        {
            "question": "What is 20% of 150?",
            "options": ["25", "30", "35", "40"],
            "correct_answer": "30",
            "step_by_step_solution": "20% = 1/5. (1/5) * 150 = 30.",
            "tips_and_tricks": "20% is equal to dividing by 5.",
            "difficulty": "easy"
        },
        {
            "question": "If the price of a commodity increases by 25%, by what percentage must consumption be reduced to keep expenditure constant?",
            "options": ["15%", "20%", "25%", "30%"],
            "correct_answer": "20%",
            "step_by_step_solution": "Reduction % = [R / (100 + R)] * 100 = [25 / 125] * 100 = (1/5) * 100 = 20%.",
            "tips_and_tricks": "Formula: R / (100+R) * 100.",
            "difficulty": "medium"
        }
    ],
    "Profit & Loss": [
        {
            "question": "An item bought for 400 is sold for 500. What is the profit percentage?",
            "options": ["15%", "20%", "25%", "30%"],
            "correct_answer": "25%",
            "step_by_step_solution": "Profit = 500 - 400 = 100. Profit % = (100 / 400) * 100 = 25%.",
            "tips_and_tricks": "Profit % is always calculated on Cost Price.",
            "difficulty": "easy"
        }
    ],
    "Simple & Compound Interest": [
        {
            "question": "Find the Simple Interest on 2000 at 5% per annum for 3 years.",
            "options": ["200", "250", "300", "350"],
            "correct_answer": "300",
            "step_by_step_solution": "SI = (P * R * T) / 100 = (2000 * 5 * 3) / 100 = 300.",
            "tips_and_tricks": "SI formula: P * R * T / 100.",
            "difficulty": "easy"
        }
    ],
    "Ratio & Proportion": [
        {
            "question": "If A:B = 2:3 and B:C = 4:5, find A:C.",
            "options": ["8:15", "6:15", "2:5", "8:12"],
            "correct_answer": "8:15",
            "step_by_step_solution": "A/C = (A/B) * (B/C) = (2/3) * (4/5) = 8/15.",
            "tips_and_tricks": "Multiply ratios directly to eliminate intermediate terms.",
            "difficulty": "easy"
        }
    ],
    "Time, Speed & Distance": [
        {
            "question": "A car covers 180 km in 3 hours. What is its speed in m/s?",
            "options": ["15 m/s", "16.67 m/s", "20 m/s", "25 m/s"],
            "correct_answer": "16.67 m/s",
            "step_by_step_solution": "Speed in km/h = 180 / 3 = 60 km/h. Convert to m/s: 60 * (5/18) = 16.67 m/s.",
            "tips_and_tricks": "Multiply km/h by 5/18 to get m/s.",
            "difficulty": "medium"
        }
    ],
    "Time & Work": [
        {
            "question": "A can finish a work in 10 days and B in 15 days. Working together, in how many days can they complete it?",
            "options": ["5 days", "6 days", "7 days", "8 days"],
            "correct_answer": "6 days",
            "step_by_step_solution": "1 day work = 1/10 + 1/15 = (3+2)/30 = 5/30 = 1/6. Total days = 6 days.",
            "tips_and_tricks": "Combined time = (A * B) / (A + B).",
            "difficulty": "easy"
        }
    ],
    "Averages": [
        {
            "question": "The average of 5 numbers is 20. If one number is excluded, average becomes 18. What is the excluded number?",
            "options": ["24", "26", "28", "30"],
            "correct_answer": "28",
            "step_by_step_solution": "Sum of 5 numbers = 5 * 20 = 100. Sum of 4 numbers = 4 * 18 = 72. Excluded number = 100 - 72 = 28.",
            "tips_and_tricks": "Difference of sums gives the excluded value.",
            "difficulty": "medium"
        }
    ],
    "Ages": [
        {
            "question": "A father is twice as old as his son. 20 years ago, father was 4 times as old as his son. What is the son's present age?",
            "options": ["20", "25", "30", "35"],
            "correct_answer": "30",
            "step_by_step_solution": "Let son = x, father = 2x. 20 years ago: 2x - 20 = 4(x - 20) => 2x - 20 = 4x - 80 => 2x = 60 => x = 30.",
            "tips_and_tricks": "Form simple linear equations for past and present ages.",
            "difficulty": "medium"
        }
    ],
    "Permutations & Combinations": [
        {
            "question": "In how many ways can 4 people sit around a circular table?",
            "options": ["6", "12", "24", "48"],
            "correct_answer": "6",
            "step_by_step_solution": "Circular permutation of n objects is (n - 1)!. Here (4 - 1)! = 3! = 6.",
            "tips_and_tricks": "Circular permutations = (n-1)!.",
            "difficulty": "easy"
        }
    ],
    "Probability": [
        {
            "question": "What is the probability of rolling a number greater than 4 on a fair six-sided die?",
            "options": ["1/6", "1/3", "1/2", "2/3"],
            "correct_answer": "1/3",
            "step_by_step_solution": "Favorable outcomes (5, 6) = 2. Total outcomes = 6. Probability = 2/6 = 1/3.",
            "tips_and_tricks": "Favorable outcomes divided by total outcomes.",
            "difficulty": "easy"
        }
    ],
    "Mixtures & Alligation": [
        {
            "question": "In what ratio must milk worth 50/L be mixed with milk worth 70/L to produce a mixture worth 55/L?",
            "options": ["3:1", "2:1", "1:3", "1:2"],
            "correct_answer": "3:1",
            "step_by_step_solution": "By Alligation: Ratio = (70 - 55) : (55 - 50) = 15 : 5 = 3:1.",
            "tips_and_tricks": "(Dearer - Mean) : (Mean - Cheaper).",
            "difficulty": "medium"
        }
    ],
    "Pipes & Cisterns": [
        {
            "question": "Pipe A fills a tank in 6 hours, Pipe B in 12 hours. Together, how long will they take to fill the tank?",
            "options": ["3 hours", "4 hours", "5 hours", "6 hours"],
            "correct_answer": "4 hours",
            "step_by_step_solution": "Net 1-hr work = 1/6 + 1/12 = 3/12 = 1/4. Total time = 4 hours.",
            "tips_and_tricks": "Combined time = (A * B) / (A + B).",
            "difficulty": "easy"
        }
    ],
    "Boats & Streams": [
        {
            "question": "A boat travels 12 km/h in still water. If stream speed is 3 km/h, what is the downstream speed?",
            "options": ["9 km/h", "12 km/h", "15 km/h", "18 km/h"],
            "correct_answer": "15 km/h",
            "step_by_step_solution": "Downstream speed = Boat speed + Stream speed = 12 + 3 = 15 km/h.",
            "tips_and_tricks": "Downstream = Boat + Stream.",
            "difficulty": "easy"
        }
    ],
    "Mensuration": [
        {
            "question": "Find the area of a circle with radius 7 cm.",
            "options": ["144 sq cm", "154 sq cm", "164 sq cm", "174 sq cm"],
            "correct_answer": "154 sq cm",
            "step_by_step_solution": "Area = π * r^2 = (22/7) * 7 * 7 = 154 sq cm.",
            "tips_and_tricks": "Remember π = 22/7.",
            "difficulty": "easy"
        }
    ],
    "Algebra": [
        {
            "question": "If x + 1/x = 3, what is x^2 + 1/x^2?",
            "options": ["7", "8", "9", "11"],
            "correct_answer": "7",
            "step_by_step_solution": "(x + 1/x)^2 = x^2 + 1/x^2 + 2 => 3^2 = x^2 + 1/x^2 + 2 => x^2 + 1/x^2 = 9 - 2 = 7.",
            "tips_and_tricks": "Formula: k^2 - 2.",
            "difficulty": "medium"
        }
    ],
    "Geometry": [
        {
            "question": "What is the sum of interior angles of a 5-sided polygon (pentagon)?",
            "options": ["360°", "450°", "540°", "720°"],
            "correct_answer": "540°",
            "step_by_step_solution": "Sum = (n - 2) * 180° = (5 - 2) * 180° = 3 * 180° = 540°.",
            "tips_and_tricks": "Formula: (n - 2) * 180°.",
            "difficulty": "easy"
        }
    ],
    "Data Interpretation": [
        {
            "question": "If a pie chart sector represents 30% of total sales, what is the central angle of this sector?",
            "options": ["90°", "108°", "120°", "135°"],
            "correct_answer": "108°",
            "step_by_step_solution": "Angle = 30% of 360° = (30/100) * 360 = 108°.",
            "tips_and_tricks": "Angle = Percentage * 3.6.",
            "difficulty": "easy"
        }
    ],
    "Logical Reasoning": [
        {
            "question": "Find the next number in series: 2, 6, 12, 20, 30, ?",
            "options": ["40", "42", "44", "46"],
            "correct_answer": "42",
            "step_by_step_solution": "Differences are +4, +6, +8, +10. Next difference is +12. 30 + 12 = 42.",
            "tips_and_tricks": "Look at the pattern of differences.",
            "difficulty": "easy"
        }
    ]
}


PREDEFINED_TEST_QUESTIONS = {
    "Number System": [
        {"question": "What is the sum of the first 20 natural numbers?", "options": ["190", "200", "210", "220"], "correct_answer": "210", "explanation": "Sum = 20*21/2 = 210", "difficulty": "medium"},
        {"question": "How many prime numbers exist between 1 and 20?", "options": ["7", "8", "9", "10"], "correct_answer": "8", "explanation": "Primes: 2, 3, 5, 7, 11, 13, 17, 19 (total 8).", "difficulty": "easy"},
        {"question": "What is the unit digit of 3^40?", "options": ["1", "3", "7", "9"], "correct_answer": "1", "explanation": "Cyclicity of 3 is 4. 40 mod 4 = 0 -> unit digit is same as 3^4 = 81 -> 1.", "difficulty": "hard"},
        {"question": "Which of the following is an irrational number?", "options": ["0.5", "√4", "√3", "22/7"], "correct_answer": "√3", "explanation": "√3 cannot be expressed as a ratio of two integers.", "difficulty": "easy"},
        {"question": "What is the remainder when 2^31 is divided by 5?", "options": ["1", "2", "3", "4"], "correct_answer": "3", "explanation": "2^1=2, 2^2=4, 2^3=8=3 mod 5, 2^4=1 mod 5. 31 mod 4 = 3 -> remainder = 3.", "difficulty": "hard"}
    ],
    "HCF & LCM": [
        {"question": "Find LCM of 15 and 20.", "options": ["30", "45", "60", "75"], "correct_answer": "60", "explanation": "LCM(15, 20) = 60.", "difficulty": "easy"},
        {"question": "The product of two numbers is 180 and their HCF is 3. Find their LCM.", "options": ["45", "50", "60", "90"], "correct_answer": "60", "explanation": "LCM = Product / HCF = 180 / 3 = 60.", "difficulty": "medium"},
        {"question": "Find HCF of 36, 54, 90.", "options": ["9", "18", "27", "36"], "correct_answer": "18", "explanation": "18 is the largest common divisor of 36, 54, and 90.", "difficulty": "medium"},
        {"question": "Find LCM of 2/3 and 3/5.", "options": ["6", "6/5", "1/15", "6/1"], "correct_answer": "6", "explanation": "LCM = LCM(2,3) / HCF(3,5) = 6 / 1 = 6.", "difficulty": "hard"},
        {"question": "Three alarm clocks ring at 4, 6, and 8 minute intervals. If they ring together at 8:00 AM, when do they ring together next?", "options": ["8:12 AM", "8:24 AM", "8:36 AM", "8:48 AM"], "correct_answer": "8:24 AM", "explanation": "LCM(4, 6, 8) = 24 minutes.", "difficulty": "medium"}
    ],
    "Percentage": [
        {"question": "What is 30% of 400?", "options": ["100", "110", "120", "130"], "correct_answer": "120", "explanation": "0.3 * 400 = 120.", "difficulty": "easy"},
        {"question": "If 60% of students in a class of 50 are girls, how many boys are there?", "options": ["15", "20", "25", "30"], "correct_answer": "20", "explanation": "Boys = 40% of 50 = 20.", "difficulty": "easy"},
        {"question": "A number is increased by 20% and then decreased by 20%. Net percentage change is?", "options": ["No change", "4% decrease", "4% increase", "2% decrease"], "correct_answer": "4% decrease", "explanation": "Net = 20 - 20 - (20*20/100) = -4%.", "difficulty": "medium"},
        {"question": "If A's income is 25% more than B's, how much % is B's income less than A's?", "options": ["20%", "25%", "30%", "33.33%"], "correct_answer": "20%", "explanation": "[25 / 125] * 100 = 20%.", "difficulty": "medium"},
        {"question": "In an exam, 70% passed in English and 80% passed in Math. 10% failed in both. If 120 passed both, total students =", "options": ["200", "240", "300", "360"], "correct_answer": "200", "explanation": "Passed at least one = 90%. Passed both = 70+80-90 = 60%. 60% of total = 120 -> Total = 200.", "difficulty": "hard"}
    ],
    "Profit & Loss": [
        {"question": "Cost price = 800, Selling price = 1000. Profit % =", "options": ["20%", "25%", "30%", "35%"], "correct_answer": "25%", "explanation": "Profit = 200. Profit % = (200/800)*100 = 25%.", "difficulty": "easy"},
        {"question": "By selling an article for 450, a man loses 10%. At what price should he sell it to gain 20%?", "options": ["500", "550", "600", "650"], "correct_answer": "600", "explanation": "CP = 450 / 0.9 = 500. Target SP = 500 * 1.2 = 600.", "difficulty": "medium"},
        {"question": "A trader marks goods 40% above CP and offers 10% discount. Profit % =", "options": ["24%", "26%", "28%", "30%"], "correct_answer": "26%", "explanation": "SP = 1.4 * 0.9 = 1.26 -> 26% profit.", "difficulty": "medium"},
        {"question": "If SP of 10 articles = CP of 12 articles, gain % =", "options": ["15%", "20%", "25%", "30%"], "correct_answer": "20%", "explanation": "Gain % = (12-10)/10 * 100 = 20%.", "difficulty": "medium"},
        {"question": "Two items sold for 990 each, one at 10% profit and other at 10% loss. Net result =", "options": ["No gain no loss", "1% loss", "1% profit", "2% loss"], "correct_answer": "1% loss", "explanation": "Loss % = (10/10)^2 = 1% loss.", "difficulty": "hard"}
    ],
    "Simple & Compound Interest": [
        {"question": "Simple interest on 5000 at 10% for 2 years =", "options": ["800", "1000", "1200", "1500"], "correct_answer": "1000", "explanation": "SI = (5000*10*2)/100 = 1000.", "difficulty": "easy"},
        {"question": "Compound interest on 10000 at 10% per annum for 2 years compounded annually =", "options": ["2000", "2100", "2200", "2300"], "correct_answer": "2100", "explanation": "A = 10000*(1.1)^2 = 12100. CI = 2100.", "difficulty": "medium"},
        {"question": "At what rate of SI will a sum double itself in 10 years?", "options": ["8%", "10%", "12%", "15%"], "correct_answer": "10%", "explanation": "SI = P => P = (P*R*10)/100 => R = 10%.", "difficulty": "easy"},
        {"question": "Difference between CI and SI on 4000 at 5% per annum for 2 years =", "options": ["10", "12", "15", "20"], "correct_answer": "10", "explanation": "Diff = P*(R/100)^2 = 4000*(5/100)^2 = 10.", "difficulty": "medium"},
        {"question": "A sum of money doubles itself in 4 years at CI. In how many years will it become 8 times itself?", "options": ["8 years", "12 years", "16 years", "20 years"], "correct_answer": "12 years", "explanation": "2^1 in 4 yrs -> 2^3 in 4*3 = 12 years.", "difficulty": "hard"}
    ],
    "Ratio & Proportion": [
        {"question": "If A:B = 3:4 and B:C = 8:9, find A:C.", "options": ["2:3", "1:2", "3:2", "4:3"], "correct_answer": "2:3", "explanation": "A/C = (3/4)*(8/9) = 24/36 = 2/3.", "difficulty": "easy"},
        {"question": "Divide 700 in the ratio 3:4 between A and B. A's share =", "options": ["300", "400", "350", "250"], "correct_answer": "300", "explanation": "A = (3/7)*700 = 300.", "difficulty": "easy"},
        {"question": "Mean proportional between 9 and 16 is =", "options": ["12", "13", "14", "15"], "correct_answer": "12", "explanation": "Mean proportional = √(9*16) = √144 = 12.", "difficulty": "medium"},
        {"question": "If 4x = 5y, then x:y =", "options": ["4:5", "5:4", "20:1", "1:20"], "correct_answer": "5:4", "explanation": "x/y = 5/4.", "difficulty": "easy"},
        {"question": "Three numbers are in ratio 2:3:4 and sum of their squares is 116. Largest number =", "options": ["4", "6", "8", "12"], "correct_answer": "8", "explanation": "(2x)^2 + (3x)^2 + (4x)^2 = 29x^2 = 116 => x^2=4 => x=2. Largest = 4x = 8.", "difficulty": "hard"}
    ],
    "Time, Speed & Distance": [
        {"question": "A car travels at 90 km/h. Speed in m/s =", "options": ["20 m/s", "25 m/s", "30 m/s", "35 m/s"], "correct_answer": "25 m/s", "explanation": "90 * (5/18) = 25 m/s.", "difficulty": "easy"},
        {"question": "Time taken to cover 300 km at 60 km/h =", "options": ["4 hrs", "5 hrs", "6 hrs", "7 hrs"], "correct_answer": "5 hrs", "explanation": "300 / 60 = 5 hours.", "difficulty": "easy"},
        {"question": "A train 150m long passes a pole in 15 seconds. Speed of train in km/h =", "options": ["30 km/h", "36 km/h", "40 km/h", "45 km/h"], "correct_answer": "36 km/h", "explanation": "Speed = 150/15 = 10 m/s = 10 * (18/5) = 36 km/h.", "difficulty": "medium"},
        {"question": "Average speed for equal distances at 20 km/h and 30 km/h =", "options": ["24 km/h", "25 km/h", "26 km/h", "27 km/h"], "correct_answer": "24 km/h", "explanation": "Avg = (2*20*30)/(20+30) = 24 km/h.", "difficulty": "medium"},
        {"question": "Two trains 100m and 120m long travel in opposite directions at 40 km/h and 32 km/h. Time to cross each other =", "options": ["9 sec", "11 sec", "13 sec", "15 sec"], "correct_answer": "11 sec", "explanation": "Rel Speed = 72 km/h = 20 m/s. Total Dist = 220m. Time = 220/20 = 11 sec.", "difficulty": "hard"}
    ],
    "Time & Work": [
        {"question": "A completes work in 12 days, B in 24 days. Together they finish in =", "options": ["6 days", "8 days", "10 days", "12 days"], "correct_answer": "8 days", "explanation": "(12*24)/(12+24) = 288/36 = 8 days.", "difficulty": "easy"},
        {"question": "15 men can complete a job in 20 days. How many men needed for 12 days?", "options": ["20", "22", "25", "30"], "correct_answer": "25", "explanation": "15*20 = M2*12 => M2 = 300/12 = 25.", "difficulty": "medium"},
        {"question": "A is twice as efficient as B. If together they finish in 14 days, A alone finishes in =", "options": ["21 days", "28 days", "35 days", "42 days"], "correct_answer": "21 days", "explanation": "Efficiency ratio 2:1. Combined = 3 units/day. Total = 3*14 = 42. A alone = 42/2 = 21 days.", "difficulty": "hard"},
        {"question": "A can do a work in 10 days, B in 15 days. They work together for 3 days, then A leaves. Days B takes to finish remaining =", "options": ["6 days", "7.5 days", "9 days", "10.5 days"], "correct_answer": "7.5 days", "explanation": "3 days work = 3*(1/10 + 1/15) = 3*(1/6) = 1/2. Remaining = 1/2. B takes (1/2)*15 = 7.5 days.", "difficulty": "hard"},
        {"question": "4 men or 6 women can do a work in 12 days. How many days will 2 men and 9 women take?", "options": ["6 days", "8 days", "10 days", "12 days"], "correct_answer": "6 days", "explanation": "4M = 6W => 1M = 1.5W. 2M + 9W = 12W. 6W take 12 days => 12W take 6 days.", "difficulty": "hard"}
    ],
    "Averages": [
        {"question": "Average of 10, 20, 30, 40, 50 =", "options": ["25", "30", "35", "40"], "correct_answer": "30", "explanation": "Sum = 150. Avg = 150/5 = 30.", "difficulty": "easy"},
        {"question": "Average of first 50 natural numbers =", "options": ["25", "25.5", "26", "50"], "correct_answer": "25.5", "explanation": "(50+1)/2 = 25.5.", "difficulty": "easy"},
        {"question": "Average marks of 30 students is 60. When teacher's mark added, avg becomes 61. Teacher's mark =", "options": ["88", "91", "92", "95"], "correct_answer": "91", "explanation": "31*61 - 30*60 = 1891 - 1800 = 91.", "difficulty": "medium"},
        {"question": "Average temperature of Mon, Tue, Wed is 37°C. Tue, Wed, Thu is 34°C. If Thu is 4/5 of Mon, Thu temp =", "options": ["32°C", "36°C", "38°C", "40°C"], "correct_answer": "36°C", "explanation": "Mon - Thu = 3*(37-34) = 9°C. Mon - 0.8Mon = 9 => 0.2Mon = 9 => Mon = 45. Thu = 36°C.", "difficulty": "hard"},
        {"question": "Mean of 100 observations was 45. Later found 83 misread as 38. Corrected mean =", "options": ["44.55", "45.45", "46.2", "47"], "correct_answer": "45.45", "explanation": "Diff = +45. New Mean = 45 + (45/100) = 45.45.", "difficulty": "medium"}
    ],
    "Ages": [
        {"question": "Sum of present ages of father and son is 60. 5 years ago, father was 4 times son's age. Son's age =", "options": ["12", "15", "18", "20"], "correct_answer": "15", "explanation": "(F-5) + (S-5) = 50. F-5 = 4(S-5) => 5(S-5) = 50 => S-5 = 10 => S = 15.", "difficulty": "medium"},
        {"question": "Ratio of ages of A and B is 3:5. Sum of ages is 40. B's age =", "options": ["15", "20", "25", "30"], "correct_answer": "25", "explanation": "B = (5/8)*40 = 25.", "difficulty": "easy"},
        {"question": "Present ratio of ages A:B = 4:5. After 5 years, ratio = 5:6. Present age of A =", "options": ["15", "20", "25", "30"], "correct_answer": "20", "explanation": "(4x+5)/(5x+5) = 5/6 => 24x + 30 = 25x + 25 => x = 5. A = 4*5 = 20.", "difficulty": "medium"},
        {"question": "A person is 24 years older than his son. In 2 years, his age will be twice his son's age. Son's present age =", "options": ["20", "22", "24", "26"], "correct_answer": "22", "explanation": "S + 24 + 2 = 2(S + 2) => S + 26 = 2S + 4 => S = 22.", "difficulty": "medium"},
        {"question": "Total ages of A, B, C is 90 years. 10 years ago, ratio was 1:2:3. C's present age =", "options": ["30", "40", "50", "60"], "correct_answer": "40", "explanation": "10 yrs ago sum = 60. Ratio 1:2:3 => C 10 yrs ago = (3/6)*60 = 30. Present C = 40.", "difficulty": "hard"}
    ],
    "Permutations & Combinations": [
        {"question": "Value of 5P2 =", "options": ["10", "20", "30", "60"], "correct_answer": "20", "explanation": "5 * 4 = 20.", "difficulty": "easy"},
        {"question": "Value of 6C3 =", "options": ["15", "20", "25", "30"], "correct_answer": "20", "explanation": "(6*5*4)/(3*2*1) = 20.", "difficulty": "easy"},
        {"question": "In how many ways can letters of 'LEADER' be arranged?", "options": ["180", "360", "720", "1440"], "correct_answer": "360", "explanation": "6 letters, 2 E's => 6! / 2! = 720 / 2 = 360.", "difficulty": "medium"},
        {"question": "How many committees of 3 can be formed from 5 people?", "options": ["10", "15", "20", "60"], "correct_answer": "10", "explanation": "5C3 = 10.", "difficulty": "easy"},
        {"question": "Number of handshakes in a room of 10 people =", "options": ["35", "45", "90", "100"], "correct_answer": "45", "explanation": "10C2 = (10*9)/2 = 45.", "difficulty": "medium"}
    ],
    "Probability": [
        {"question": "Probability of getting a head on a single coin toss =", "options": ["0", "1/4", "1/2", "1"], "correct_answer": "1/2", "explanation": "Favorable = 1, Total = 2.", "difficulty": "easy"},
        {"question": "Two coins are tossed. Probability of getting 2 heads =", "options": ["1/4", "1/2", "3/4", "1"], "correct_answer": "1/4", "explanation": "Outcomes: HH, HT, TH, TT. P(HH) = 1/4.", "difficulty": "easy"},
        {"question": "Probability of drawing a Red Ace from a deck of 52 cards =", "options": ["1/52", "2/52", "4/52", "13/52"], "correct_answer": "2/52", "explanation": "2 red aces (Heart, Diamond). 2/52 = 1/26.", "difficulty": "medium"},
        {"question": "A bag contains 3 red and 5 blue balls. Probability of drawing a red ball =", "options": ["3/8", "5/8", "3/5", "1/3"], "correct_answer": "3/8", "explanation": "3 / (3+5) = 3/8.", "difficulty": "easy"},
        {"question": "Two dice rolled. Probability of sum being 7 =", "options": ["1/6", "5/36", "7/36", "1/12"], "correct_answer": "1/6", "explanation": "Pairs: (1,6),(2,5),(3,4),(4,3),(5,2),(6,1) = 6 pairs. 6/36 = 1/6.", "difficulty": "hard"}
    ],
    "Mixtures & Alligation": [
        {"question": "Mix sugar at 40/kg and 60/kg to get 50/kg mixture. Ratio =", "options": ["1:1", "1:2", "2:1", "3:2"], "correct_answer": "1:1", "explanation": "(60-50):(50-40) = 10:10 = 1:1.", "difficulty": "easy"},
        {"question": "In 40 liters mixture of milk and water, ratio is 3:1. How much water added to make ratio 2:1?", "options": ["5L", "6.67L", "8L", "10L"], "correct_answer": "5L", "explanation": "Milk = 30L, Water = 10L. Target ratio 30/(10+x) = 2/1 => 10+x = 15 => x = 5L.", "difficulty": "medium"},
        {"question": "A vessel contains 80L wine. 8L removed and replaced with water. Process repeated once more. Wine left =", "options": ["64.8L", "65.2L", "66.4L", "67.8L"], "correct_answer": "64.8L", "explanation": "80 * (1 - 8/80)^2 = 80 * (0.9)^2 = 80 * 0.81 = 64.8L.", "difficulty": "hard"},
        {"question": "In what ratio water be mixed with milk to gain 20% by selling at cost price?", "options": ["1:4", "1:5", "1:6", "2:5"], "correct_answer": "1:5", "explanation": "Water:Milk = Gain%:100% = 20:100 = 1:5.", "difficulty": "medium"},
        {"question": "Two alloys contain copper and zinc in ratio 2:3 and 4:1. Mixed in equal quantities, final ratio =", "options": ["3:2", "4:3", "7:5", "1:1"], "correct_answer": "3:2", "explanation": "Copper = 2/5 + 4/5 = 6/5. Zinc = 3/5 + 1/5 = 4/5. Ratio = 6:4 = 3:2.", "difficulty": "hard"}
    ],
    "Pipes & Cisterns": [
        {"question": "Pipe A fills in 10 hours, B in 15 hours. Both open together fill in =", "options": ["5 hrs", "6 hrs", "7.5 hrs", "8 hrs"], "correct_answer": "6 hrs", "explanation": "(10*15)/(10+15) = 150/25 = 6 hrs.", "difficulty": "easy"},
        {"question": "A pipe fills tank in 8 hrs, leak empties in 10 hrs. Tank fills in =", "options": ["30 hrs", "40 hrs", "50 hrs", "60 hrs"], "correct_answer": "40 hrs", "explanation": "Net work = 1/8 - 1/10 = 1/40 -> 40 hrs.", "difficulty": "medium"},
        {"question": "Pipe A fills in 12 min, B in 16 min. If both opened together, after how many minutes should B be closed so tank fills in 9 min?", "options": ["3 min", "4 min", "4.5 min", "6 min"], "correct_answer": "4 min", "explanation": "A works 9 min = 9/12 = 3/4 work. B does 1/4 work. B rate = 1/16 -> Time = (1/4)*16 = 4 min.", "difficulty": "hard"},
        {"question": "Three pipes A, B, C fill tank in 6 hours. After 2 hours C is closed, A & B fill in 7 hours. C alone fills in =", "options": ["10 hrs", "12 hrs", "14 hrs", "16 hrs"], "correct_answer": "14 hrs", "explanation": "2 hrs all work = 1/3. Remaining 2/3 done by A+B in 7 hrs -> A+B full in 10.5 hrs. C rate = 1/6 - 1/10.5 = 1/14 -> 14 hrs.", "difficulty": "hard"},
        {"question": "Pipe A is 3 times faster than B. Together they fill in 18 min. B alone fills in =", "options": ["54 min", "72 min", "90 min", "108 min"], "correct_answer": "72 min", "explanation": "A+B rate = 4 units/min. Total = 4*18 = 72 units. B rate = 1 unit/min -> 72 min.", "difficulty": "hard"}
    ],
    "Boats & Streams": [
        {"question": "Boat speed in still water = 15 km/h, Stream = 3 km/h. Upstream speed =", "options": ["9 km/h", "12 km/h", "15 km/h", "18 km/h"], "correct_answer": "12 km/h", "explanation": "15 - 3 = 12 km/h.", "difficulty": "easy"},
        {"question": "Downstream speed = 18 km/h, Upstream speed = 10 km/h. Speed of boat in still water =", "options": ["12 km/h", "14 km/h", "15 km/h", "16 km/h"], "correct_answer": "14 km/h", "explanation": "(18+10)/2 = 14 km/h.", "difficulty": "easy"},
        {"question": "Downstream speed = 20 km/h, Upstream speed = 12 km/h. Speed of stream =", "options": ["4 km/h", "5 km/h", "6 km/h", "8 km/h"], "correct_answer": "4 km/h", "explanation": "(20-12)/2 = 4 km/h.", "difficulty": "easy"},
        {"question": "A boat goes 24 km downstream in 3 hrs and 24 km upstream in 6 hrs. Speed of boat =", "options": ["5 km/h", "6 km/h", "7 km/h", "8 km/h"], "correct_answer": "6 km/h", "explanation": "D = 8, U = 4. Boat = (8+4)/2 = 6 km/h.", "difficulty": "medium"},
        {"question": "A man can row 6 km/h in still water. If river flows at 2 km/h, takes 3 hours to row to a place and back. Distance =", "options": ["6 km", "8 km", "10 km", "12 km"], "correct_answer": "8 km", "explanation": "D=8, U=4. x/8 + x/4 = 3 => 3x/8 = 3 => x = 8 km.", "difficulty": "hard"}
    ],
    "Mensuration": [
        {"question": "Perimeter of square with side 5 cm =", "options": ["15 cm", "20 cm", "25 cm", "30 cm"], "correct_answer": "20 cm", "explanation": "4 * 5 = 20 cm.", "difficulty": "easy"},
        {"question": "Area of rectangle length 10 cm and breadth 6 cm =", "options": ["50 sq cm", "60 sq cm", "70 sq cm", "80 sq cm"], "correct_answer": "60 sq cm", "explanation": "10 * 6 = 60 sq cm.", "difficulty": "easy"},
        {"question": "Volume of cube of side 4 cm =", "options": ["16 cm^3", "32 cm^3", "64 cm^3", "128 cm^3"], "correct_answer": "64 cm^3", "explanation": "4^3 = 64 cm^3.", "difficulty": "easy"},
        {"question": "Volume of cylinder with radius 7 cm and height 10 cm =", "options": ["1440 cm^3", "1540 cm^3", "1640 cm^3", "1740 cm^3"], "correct_answer": "1540 cm^3", "explanation": "(22/7)*7*7*10 = 1540 cm^3.", "difficulty": "medium"},
        {"question": "Diagonal of square with area 50 sq cm =", "options": ["5 cm", "10 cm", "12 cm", "14 cm"], "correct_answer": "10 cm", "explanation": "a^2 = 50 => a = 5√2. Diagonal = a√2 = 10 cm.", "difficulty": "medium"}
    ],
    "Algebra": [
        {"question": "Solve for x: 2x + 5 = 15", "options": ["3", "4", "5", "6"], "correct_answer": "5", "explanation": "2x = 10 => x = 5.", "difficulty": "easy"},
        {"question": "If x - 1/x = 4, then x^2 + 1/x^2 =", "options": ["14", "16", "18", "20"], "correct_answer": "18", "explanation": "(x-1/x)^2 + 2 = 16 + 2 = 18.", "difficulty": "medium"},
        {"question": "Roots of quadratic x^2 - 5x + 6 = 0 =", "options": ["1, 6", "2, 3", "-2, -3", "-1, -6"], "correct_answer": "2, 3", "explanation": "(x-2)(x-3) = 0 => x = 2, 3.", "difficulty": "medium"},
        {"question": "Value of (a+b)^2 - (a-b)^2 =", "options": ["2ab", "4ab", "a^2+b^2", "2(a^2+b^2)"], "correct_answer": "4ab", "explanation": "Identity expansion gives 4ab.", "difficulty": "easy"},
        {"question": "If a + b = 7 and ab = 12, then a^2 + b^2 =", "options": ["25", "29", "33", "37"], "correct_answer": "25", "explanation": "(a+b)^2 - 2ab = 49 - 24 = 25.", "difficulty": "medium"}
    ],
    "Geometry": [
        {"question": "Sum of angles in a triangle =", "options": ["90°", "180°", "270°", "360°"], "correct_answer": "180°", "explanation": "Triangle angles total 180°.", "difficulty": "easy"},
        {"question": "In right triangle, base=6, height=8. Hypotenuse =", "options": ["9", "10", "11", "12"], "correct_answer": "10", "explanation": "√(36+64) = √100 = 10.", "difficulty": "easy"},
        {"question": "Each interior angle of regular hexagon (6 sides) =", "options": ["108°", "120°", "135°", "144°"], "correct_answer": "120°", "explanation": "(6-2)*180 / 6 = 720 / 6 = 120°.", "difficulty": "medium"},
        {"question": "Angle in a semi-circle is always =", "options": ["45°", "60°", "90°", "180°"], "correct_answer": "90°", "explanation": "Thales's theorem: angle in semicircle is 90°.", "difficulty": "easy"},
        {"question": "Number of diagonals in a 8-sided polygon (octagon) =", "options": ["16", "20", "24", "28"], "correct_answer": "20", "explanation": "n(n-3)/2 = 8*5/2 = 20.", "difficulty": "hard"}
    ],
    "Data Interpretation": [
        {"question": "If total revenue is 50,000 and profit is 10,000, profit percentage =", "options": ["15%", "20%", "25%", "30%"], "correct_answer": "20%", "explanation": "(10000/50000)*100 = 20%.", "difficulty": "easy"},
        {"question": "Average of values 120, 140, 160, 180, 200 =", "options": ["150", "160", "170", "180"], "correct_answer": "160", "explanation": "Symmetric AP average = middle value = 160.", "difficulty": "easy"},
        {"question": "If production increases from 400 to 500 units, percentage increase =", "options": ["20%", "25%", "30%", "35%"], "correct_answer": "25%", "explanation": "(100/400)*100 = 25%.", "difficulty": "easy"},
        {"question": "In bar graph, A=40, B=60, C=80. Ratio of A to (B+C) =", "options": ["1:2", "2:7", "1:3.5", "2:5"], "correct_answer": "2:7", "explanation": "40 : 140 = 2:7.", "difficulty": "medium"},
        {"question": "If 45% of 800 employees are male, number of female employees =", "options": ["360", "400", "440", "480"], "correct_answer": "440", "explanation": "Females = 55% of 800 = 440.", "difficulty": "medium"}
    ],
    "Logical Reasoning": [
        {"question": "Next term in series: 5, 10, 20, 40, ?", "options": ["50", "60", "70", "80"], "correct_answer": "80", "explanation": "Double each term: 40 * 2 = 80.", "difficulty": "easy"},
        {"question": "If CAT is coded as 3120, how is DOG coded? (A=1, B=2...)", "options": ["4157", "41515", "4157", "4157"], "correct_answer": "4157", "explanation": "D=4, O=15, G=7 -> 4157.", "difficulty": "easy"},
        {"question": "Point A is 10m North of B. C is 10m East of B. Direction of C from A =", "options": ["North-East", "South-East", "South-West", "North-West"], "correct_answer": "South-East", "explanation": "From A, moving South brings to B, then East brings to C -> South-East.", "difficulty": "medium"},
        {"question": "All cats are mammals. All mammals are animals. Conclusion: All cats are animals.", "options": ["Definitely True", "Definitely False", "Cannot say", "Irrelevant"], "correct_answer": "Definitely True", "explanation": "Syllogism valid chain: Cats ⊂ Mammals ⊂ Animals.", "difficulty": "easy"},
        {"question": "Find odd one out: 27, 64, 125, 144, 216", "options": ["27", "64", "125", "144"], "correct_answer": "144", "explanation": "27=3^3, 64=4^3, 125=5^3, 216=6^3. 144 is 12^2 (square, not cube).", "difficulty": "medium"}
    ]
}
