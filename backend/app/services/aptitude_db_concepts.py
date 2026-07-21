# Pre-generated database concepts for Aptitude Training topics

PREDEFINED_CONCEPTS = {
    "Number System": {
        "topic": "Number System",
        "concepts": [
            {
                "title": "Types of Numbers & Divisibility",
                "description": "Natural numbers (1, 2, 3...), Whole numbers (0, 1, 2...), Integers, Rational, and Irrational numbers. A number is divisible by 3 if the sum of its digits is divisible by 3. Divisibility by 4 requires the last two digits to be divisible by 4.",
                "formula": "Sum of first n natural numbers = n(n+1)/2",
                "example": "Find the sum of the first 20 natural numbers. Solution: 20 * 21 / 2 = 210."
            },
            {
                "title": "Prime Numbers & Unit Digit Rules",
                "description": "Prime numbers have only two distinct positive divisors: 1 and themselves. To find the unit digit of a high power a^b, use the cyclicity of the unit digit of 'a' (cyclicity of 2,3,7,8 is 4; cyclicity of 4,9 is 2; 0,1,5,6 is 1).",
                "formula": "N = p^a * q^b => Total Factors = (a+1)(b+1)",
                "example": "Find the unit digit of 7^35. 35 mod 4 = 3, so unit digit is same as 7^3 = 343 -> 3."
            }
        ],
        "tips_and_tricks": [
            "Sum of first n even numbers = n(n+1)",
            "Sum of first n odd numbers = n^2",
            "Always check divisibility rules starting from 2, 3, 5, 9, 11 for rapid elimination."
        ],
        "key_points": [
            "2 is the only even prime number.",
            "1 is neither prime nor composite.",
            "Product of two consecutive integers is always even."
        ]
    },

    "HCF & LCM": {
        "topic": "HCF & LCM",
        "concepts": [
            {
                "title": "Definitions & Basic Formula",
                "description": "HCF (Highest Common Factor) is the greatest number that divides given numbers. LCM (Lowest Common Multiple) is the smallest number divisible by given numbers.",
                "formula": "HCF * LCM = Product of two numbers",
                "example": "Find HCF and LCM of 12 and 18. HCF = 6, LCM = 36. Product = 12 * 18 = 216. HCF * LCM = 6 * 36 = 216."
            },
            {
                "title": "Fractions HCF and LCM",
                "description": "To find HCF of fractions, calculate HCF of numerators divided by LCM of denominators. For LCM of fractions, calculate LCM of numerators divided by HCF of denominators.",
                "formula": "HCF(a/b, c/d) = HCF(a,c) / LCM(b,d)",
                "example": "Find HCF of 2/3 and 4/5. HCF(2,4) / LCM(3,5) = 2 / 15."
            }
        ],
        "tips_and_tricks": [
            "LCM of co-prime numbers is their direct product.",
            "For bells ringing together, calculate the LCM of their individual intervals."
        ],
        "key_points": [
            "HCF is always a factor of LCM.",
            "Co-prime numbers have an HCF of 1."
        ]
    },

    "Percentage": {
        "topic": "Percentage",
        "concepts": [
            {
                "title": "Percentage Fundamentals & Conversions",
                "description": "A percentage represents a fraction out of 100. To convert a fraction to percentage, multiply by 100. Key fraction equivalents: 1/2 = 50%, 1/3 = 33.33%, 1/4 = 25%, 1/5 = 20%, 1/6 = 16.67%, 1/8 = 12.5%.",
                "formula": "Percentage = (Part / Whole) * 100",
                "example": "If a student scores 45 out of 60, percentage = (45/60)*100 = 75%."
            },
            {
                "title": "Successive Percentage Changes",
                "description": "When a value is changed by x% and then by y%, the net percentage change can be computed directly using the net formula.",
                "formula": "Net Change % = x + y + (xy / 100)",
                "example": "A salary increases by 10% then 20%. Net increase = 10 + 20 + (10*20/100) = 32%."
            }
        ],
        "tips_and_tricks": [
            "x% of y is always equal to y% of x. (e.g. 16% of 50 = 50% of 16 = 8).",
            "If price increases by R%, consumption must decrease by [R / (100+R)] * 100 to keep expenditure constant."
        ],
        "key_points": [
            "Percentage increase = (Increase / Original Value) * 100",
            "Percentage decrease = (Decrease / Original Value) * 100"
        ]
    },

    "Profit & Loss": {
        "topic": "Profit & Loss",
        "concepts": [
            {
                "title": "Cost Price, Selling Price & Markup",
                "description": "Cost Price (CP) is purchasing price. Selling Price (SP) is selling price. Marked Price (MP) is the list price before discount.",
                "formula": "Profit = SP - CP | Loss = CP - SP | Profit % = (Profit/CP)*100 | Loss % = (Loss/CP)*100",
                "example": "CP = 500, SP = 600. Profit = 100. Profit % = (100/500)*100 = 20%."
            },
            {
                "title": "Discount and False Weights",
                "description": "Discount is always calculated on Marked Price (MP). SP = MP * (100 - Discount%)/100.",
                "formula": "Gain % using False Weight = [ Error / (True Value - Error) ] * 100",
                "example": "A trader uses 900g instead of 1kg. Gain % = [ 100 / (1000 - 100) ] * 100 = (100/900)*100 = 11.11%."
            }
        ],
        "tips_and_tricks": [
            "When two items are sold at the same price, one at x% profit and another at x% loss, there is an overall loss of (x/10)^2 %.",
            "Markup % = [(MP - CP) / CP] * 100."
        ],
        "key_points": [
            "Profit or loss is always calculated on Cost Price unless specified otherwise.",
            "Discount is always calculated on Marked Price."
        ]
    },

    "Simple & Compound Interest": {
        "topic": "Simple & Compound Interest",
        "concepts": [
            {
                "title": "Simple Interest (SI)",
                "description": "Interest calculated uniformally on the principal amount throughout the entire period.",
                "formula": "SI = (P * R * T) / 100 | Total Amount = P + SI",
                "example": "P = 1000, R = 10%, T = 2 years. SI = (1000*10*2)/100 = 200. Total = 1200."
            },
            {
                "title": "Compound Interest (CI)",
                "description": "Interest calculated on the principal plus any previously accumulated interest (compounding).",
                "formula": "A = P * (1 + R/100)^T | CI = A - P",
                "example": "P = 1000, R = 10%, T = 2 years. A = 1000 * (1.1)^2 = 1210. CI = 210."
            }
        ],
        "tips_and_tricks": [
            "Difference between CI and SI for 2 years = P * (R/100)^2",
            "Rule of 72: Doubling time for money at R% CI ≈ 72 / R years."
        ],
        "key_points": [
            "For 1 year compounded annually, SI and CI are equal.",
            "If interest is compounded half-yearly, rate becomes R/2 and time becomes 2T."
        ]
    },

    "Ratio & Proportion": {
        "topic": "Ratio & Proportion",
        "concepts": [
            {
                "title": "Ratios & Proportion Principles",
                "description": "A ratio compares two quantities of the same unit. Proportion states that two ratios are equal: a:b = c:d.",
                "formula": "If a:b = c:d, then a*d = b*c (Product of extremes = Product of means)",
                "example": "If 2:5 = x:20, then 2*20 = 5*x => 5x = 40 => x = 8."
            },
            {
                "title": "Mean Proportion & Partnerships",
                "description": "Mean proportional between a and b is √(a*b). In partnership, profits are divided in the ratio of (Capital * Time).",
                "formula": "Profit Ratio = (P1 * T1) : (P2 * T2)",
                "example": "A invests 1000 for 12 months, B invests 2000 for 6 months. Profit ratio = (1000*12) : (2000*6) = 12000 : 12000 = 1:1."
            }
        ],
        "tips_and_tricks": [
            "If A:B = 2:3 and B:C = 4:5, multiply A:B by 4 and B:C by 3 to get A:B:C = 8:12:15.",
            "Duplicate ratio of a:b is a^2:b^2."
        ],
        "key_points": [
            "Ratio remains unchanged when multiplied or divided by the same non-zero number.",
            "Sub-duplicate ratio of a:b is √a : √b."
        ]
    },

    "Time, Speed & Distance": {
        "topic": "Time, Speed & Distance",
        "concepts": [
            {
                "title": "Basic Relationships & Unit Conversions",
                "description": "Speed is distance covered per unit time. Convert km/h to m/s by multiplying by 5/18. Convert m/s to km/h by multiplying by 18/5.",
                "formula": "Speed = Distance / Time | Distance = Speed * Time | Time = Distance / Speed",
                "example": "Convert 72 km/h to m/s: 72 * (5/18) = 20 m/s."
            },
            {
                "title": "Average Speed & Train Problems",
                "description": "Average speed is total distance divided by total time. When a train passes a pole/person, distance = train length. When passing a platform/bridge, distance = train length + platform length.",
                "formula": "Average Speed (for equal distances) = 2xy / (x + y)",
                "example": "A travels to a spot at 20 km/h and returns at 30 km/h. Avg speed = 2*20*30 / (20+30) = 1200 / 50 = 24 km/h."
            }
        ],
        "tips_and_tricks": [
            "Relative Speed: Opposite directions -> S1 + S2 | Same direction -> |S1 - S2|",
            "Distance is directly proportional to speed when time is constant."
        ],
        "key_points": [
            "Unit consistency is crucial: km with hours, meters with seconds.",
            "Average speed is NOT simple arithmetic mean of speeds."
        ]
    },

    "Time & Work": {
        "topic": "Time & Work",
        "concepts": [
            {
                "title": "Work Efficiency & Rate Concepts",
                "description": "If a person completes a job in N days, 1 day work rate = 1/N of the total work.",
                "formula": "Total Work = Efficiency * Time | (M1 * D1 * H1) / W1 = (M2 * D2 * H2) / W2",
                "example": "A does a work in 10 days, B in 15 days. Combined 1-day work = 1/10 + 1/15 = 1/6. Together they finish in 6 days."
            },
            {
                "title": "Man-Days & Alternate Days Work",
                "description": "If 12 men can build a wall in 6 days, work = 12 * 6 = 72 man-days. Alternate day problems require calculating combined work in cycles.",
                "formula": "M1 * D1 = M2 * D2",
                "example": "If 10 workers complete work in 12 days, how many days for 15 workers? 10*12 = 15*D2 => D2 = 8 days."
            }
        ],
        "tips_and_tricks": [
            "Assume Total Work as the LCM of individual completion times for easy integer calculations.",
            "Efficiency is inversely proportional to time taken."
        ],
        "key_points": [
            "If A is twice as efficient as B, ratio of time taken A:B = 1:2.",
            "Wages are distributed in ratio of daily work done (Efficiency)."
        ]
    },

    "Averages": {
        "topic": "Averages",
        "concepts": [
            {
                "title": "Arithmetic Mean & Weighted Average",
                "description": "Average is the sum of all observations divided by the total number of observations.",
                "formula": "Average = Sum of items / Number of items | Weighted Avg = (n1*a1 + n2*a2) / (n1 + n2)",
                "example": "Average of 10, 20, 30 = (10+20+30)/3 = 20."
            },
            {
                "title": "Inclusion, Exclusion & Replacement",
                "description": "When a new item is added to a group, the new total sum = Old Sum + New Item. If average changes by ΔA, New Item = Old Avg + (New Number of items * ΔA).",
                "formula": "New Sum = (Old Avg * Old Count) + New Value",
                "example": "Avg age of 5 boys is 12. With teacher included, avg becomes 14. Teacher's age = (6 * 14) - (5 * 12) = 84 - 60 = 24."
            }
        ],
        "tips_and_tricks": [
            "Average of first n consecutive natural numbers = (n + 1) / 2.",
            "Average of an arithmetic progression (AP) is always (First term + Last term) / 2."
        ],
        "key_points": [
            "If every observation is multiplied by k, the average is also multiplied by k.",
            "Deviation method speeds up large number average calculations."
        ]
    },

    "Ages": {
        "topic": "Ages",
        "concepts": [
            {
                "title": "Age Linear Equations & Ratio Rules",
                "description": "Age problems involve setting up linear equations representing present age (x), age n years ago (x-n), and age n years hence (x+n).",
                "formula": "Present Age = x | Age n years ago = x - n | Age after n years = x + n",
                "example": "Father is 3 times son's age. Sum of ages is 48. 3x + x = 48 => 4x = 48 => x = 12 (Son), Father = 36."
            }
        ],
        "tips_and_tricks": [
            "The age difference between two people remains CONSTANT at all times.",
            "If ratio of ages changes over time, equate the constant difference between ratios."
        ],
        "key_points": [
            "Always assume present ages as variables unless specified otherwise.",
            "Cross-multiplication of ratio differences saves calculation time."
        ]
    },

    "Permutations & Combinations": {
        "topic": "Permutations & Combinations",
        "concepts": [
            {
                "title": "Factorial, Permutations (Arrangement) & Combinations (Selection)",
                "description": "Permutation is an ordered arrangement. Combination is a selection where order does not matter.",
                "formula": "nPn = n! | nPr = n! / (n-r)! | nCr = n! / [r!(n-r)!]",
                "example": "In how many ways can 3 letters out of 5 be selected? 5C3 = 5*4*3 / (3*2*1) = 10."
            }
        ],
        "tips_and_tricks": [
            "nCr = nC(n-r). (e.g. 10C8 = 10C2 = 45).",
            "Circular permutation of n objects = (n-1)!"
        ],
        "key_points": [
            "Use 'AND' -> Multiply options | Use 'OR' -> Add options.",
            "0! = 1."
        ]
    },

    "Probability": {
        "topic": "Probability",
        "concepts": [
            {
                "title": "Basic Probability & Sample Space",
                "description": "Probability measures the likelihood of an event occurring between 0 (impossible) and 1 (certain).",
                "formula": "P(E) = Number of Favorable Outcomes / Total Sample Space Outcomes",
                "example": "Probability of getting a head on a coin flip = 1/2."
            },
            {
                "title": "Complementary & Independent Events",
                "description": "P(Event happens) + P(Event does not happen) = 1. For independent events A and B, P(A and B) = P(A) * P(B).",
                "formula": "P(E') = 1 - P(E)",
                "example": "Probability of rolling a 6 on a die is 1/6. Probability of NOT rolling 6 = 1 - 1/6 = 5/6."
            }
        ],
        "tips_and_tricks": [
            "When rolling two dice, total outcomes = 36.",
            "When tossing n coins, total outcomes = 2^n."
        ],
        "key_points": [
            "0 <= P(E) <= 1 always.",
            "Sum of probabilities of all elementary events is 1."
        ]
    },

    "Mixtures & Alligation": {
        "topic": "Mixtures & Alligation",
        "concepts": [
            {
                "title": "Alligation Rule",
                "description": "Alligation is a rule for finding the ratio in which two or more ingredients at given prices must be mixed to produce a mixture at a desired mean price.",
                "formula": "(Cheaper Quantity / Dearer Quantity) = (Dearer Price - Mean Price) / (Mean Price - Cheaper Price)",
                "example": "Mix tea at 60/kg and 90/kg to get 75/kg mixture. Ratio = (90-75)/(75-60) = 15/15 = 1:1."
            }
        ],
        "tips_and_tricks": [
            "Repeated Dilution Formula: Remaining Pure Liquid = Initial * (1 - x/V)^n",
            "Alligation works on average rates, speeds, percentages, and costs."
        ],
        "key_points": [
            "Mean price must always lie strictly between the cheaper and dearer prices.",
            "Ensure units are consistent across all terms."
        ]
    },

    "Pipes & Cisterns": {
        "topic": "Pipes & Cisterns",
        "concepts": [
            {
                "title": "Inlet & Outlet Pipe Rates",
                "description": "Inlet pipe fills tank (+ rate). Outlet pipe empties tank (- rate).",
                "formula": "Net 1 hour work = (1/Fill Time) - (1/Empty Time)",
                "example": "Pipe A fills in 4 hours, Pipe B empties in 6 hours. Net 1 hour work = 1/4 - 1/6 = 1/12. Tank fills in 12 hours."
            }
        ],
        "tips_and_tricks": [
            "Treat tank capacity as LCM of pipe individual hours.",
            "Inlet work is positive, outlet leak work is negative."
        ],
        "key_points": [
            "If net result is negative, the tank is being emptied.",
            "Always check which pipes are open simultaneously."
        ]
    },

    "Boats & Streams": {
        "topic": "Boats & Streams",
        "concepts": [
            {
                "title": "Downstream & Upstream Speeds",
                "description": "Let boat speed in still water be B, stream speed be S. Downstream (with flow) = B + S. Upstream (against flow) = B - S.",
                "formula": "Downstream D = B + S | Upstream U = B - S | B = (D + U)/2 | S = (D - U)/2",
                "example": "Boat speed 10 km/h, stream 2 km/h. Downstream = 12 km/h, Upstream = 8 km/h."
            }
        ],
        "tips_and_tricks": [
            "Speed of boat = (Downstream Speed + Upstream Speed) / 2",
            "Speed of stream = (Downstream Speed - Upstream Speed) / 2"
        ],
        "key_points": [
            "Downstream speed is always greater than upstream speed.",
            "Boat speed must be greater than stream speed to move upstream."
        ]
    },

    "Mensuration": {
        "topic": "Mensuration",
        "concepts": [
            {
                "title": "2D & 3D Formulas",
                "description": "Calculations of area, perimeter, surface area, and volume for geometric figures.",
                "formula": "Circle Area = πr^2, Circumference = 2πr | Cylinder Volume = πr^2h | Sphere Volume = (4/3)πr^3",
                "example": "Radius of circle is 7. Area = (22/7)*7*7 = 154."
            }
        ],
        "tips_and_tricks": [
            "Diagonal of square of side a = a√2.",
            "Total Surface Area of Cube = 6a^2 | Volume = a^3."
        ],
        "key_points": [
            "1 liter = 1000 cm^3 | 1 m^3 = 1000 liters.",
            "Area is always in square units, Volume in cubic units."
        ]
    },

    "Algebra": {
        "topic": "Algebra",
        "concepts": [
            {
                "title": "Algebraic Identities & Quadratics",
                "description": "Standard identities for expanding and factoring expressions.",
                "formula": "(a+b)^2 = a^2 + 2ab + b^2 | (a-b)^2 = a^2 - 2ab + b^2 | a^2 - b^2 = (a-b)(a+b)",
                "example": "If x + 1/x = 4, then x^2 + 1/x^2 = 4^2 - 2 = 14."
            }
        ],
        "tips_and_tricks": [
            "If x + 1/x = k, then x^2 + 1/x^2 = k^2 - 2.",
            "If x + 1/x = k, then x^3 + 1/x^3 = k^3 - 3k."
        ],
        "key_points": [
            "For quadratic ax^2 + bx + c = 0, roots sum = -b/a, roots product = c/a.",
            "Discriminant D = b^2 - 4ac."
        ]
    },

    "Geometry": {
        "topic": "Geometry",
        "concepts": [
            {
                "title": "Triangles & Circles Properties",
                "description": "Properties of angles, triangles, circles, and parallel lines.",
                "formula": "Sum of angles of triangle = 180° | Pythagoras theorem: a^2 + b^2 = c^2",
                "example": "In right-angled triangle with sides 3 and 4, hypotenuse = √(3^2 + 4^2) = 5."
            }
        ],
        "tips_and_tricks": [
            "Exterior angle of a triangle equals sum of two opposite interior angles.",
            "Angle subtended by an arc at the center is double the angle subtended at the circumference."
        ],
        "key_points": [
            "Sum of interior angles of n-sided polygon = (n-2) * 180°.",
            "Tangents from external point to a circle are equal in length."
        ]
    },

    "Data Interpretation": {
        "topic": "Data Interpretation",
        "concepts": [
            {
                "title": "Bar Charts, Pie Charts & Tables",
                "description": "Reading and extracting insights from tabular data, pie charts, and bar graphs.",
                "formula": "Sector Angle in Pie Chart = (Category Value / Total Value) * 360°",
                "example": "If category is 25% of total, pie chart angle = 0.25 * 360 = 90°."
            }
        ],
        "tips_and_tricks": [
            "Use approximation for quick division when evaluating chart data.",
            "Focus on percentages and ratios rather than large exact numbers."
        ],
        "key_points": [
            "Always check chart titles, scales, and legend units carefully.",
            "Calculate percentage change using (Final - Initial) / Initial * 100."
        ]
    },

    "Logical Reasoning": {
        "topic": "Logical Reasoning",
        "concepts": [
            {
                "title": "Series, Syllogisms & Seating Arrangements",
                "description": "Identifying patterns in series, evaluating logical syllogisms, and arranging positions.",
                "formula": "Number of persons in row = (Rank from Left + Rank from Right) - 1",
                "example": "Ravi is 10th from left and 15th from right in a row. Total students = 10 + 15 - 1 = 24."
            }
        ],
        "tips_and_tricks": [
            "Draw simple Venn diagrams for Syllogism questions.",
            "For direction problems, draw N-S-E-W axis at every decision step."
        ],
        "key_points": [
            "Do not assume outside real-world information in logical statements.",
            "Read conditions step-by-step for seating arrangement puzzles."
        ]
    }
}
