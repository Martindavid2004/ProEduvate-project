import React, { useState } from 'react';
import { Play, RotateCcw, CheckCircle, XCircle, Clock, Trophy, Code } from 'lucide-react';
import CodeEditor from '@uiw/react-textarea-code-editor';

const CodingInterface = ({ onClose, language = 'python' }) => {
  const [code, setCode] = useState('');
  const [output, setOutput] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [testResults, setTestResults] = useState(null);
  const [currentProblemIndex, setCurrentProblemIndex] = useState(0);
  
  const pythonProblems = [
    {
      id: 1,
      title: 'Sum of Two Numbers',
      difficulty: 'Easy',
      description: 'Write a function that takes two numbers as input and returns their sum.',
      examples: [
        { input: 'a = 5, b = 3', output: '8' },
        { input: 'a = -2, b = 7', output: '5' },
      ],
      testCases: [
        { input: '5\n3', expectedOutput: '8' },
        { input: '-2\n7', expectedOutput: '5' },
        { input: '100\n200', expectedOutput: '300' },
      ],
      starterCode: '# Read two numbers from input\na = int(input())\nb = int(input())\n\n# Write your code here\nresult = 0  # Calculate sum\n\nprint(result)'
    },
    {
      id: 2,
      title: 'Reverse a String',
      difficulty: 'Easy',
      description: 'Write a function that takes a string as input and returns the string reversed.',
      examples: [
        { input: '"hello"', output: '"olleh"' },
        { input: '"Python"', output: '"nohtyP"' },
      ],
      testCases: [
        { input: 'hello', expectedOutput: 'olleh' },
        { input: 'Python', expectedOutput: 'nohtyP' },
        { input: 'abcdef', expectedOutput: 'fedcba' },
      ],
      starterCode: '# Read string from input\ntext = input()\n\n# Write your code here\nreversed_text = ""  # Reverse the string\n\nprint(reversed_text)'
    },
    {
      id: 3,
      title: 'Find Maximum Number',
      difficulty: 'Easy',
      description: 'Write a function that finds the maximum number in a list of integers.',
      examples: [
        { input: '[1, 5, 3, 9, 2]', output: '9' },
        { input: '[-5, -2, -10, -1]', output: '-1' },
      ],
      testCases: [
        { input: '1 5 3 9 2', expectedOutput: '9' },
        { input: '-5 -2 -10 -1', expectedOutput: '-1' },
        { input: '100 50 200 75', expectedOutput: '200' },
      ],
      starterCode: '# Read numbers from input\nnumbers = list(map(int, input().split()))\n\n# Write your code here\nmax_num = 0  # Find maximum\n\nprint(max_num)'
    },
    {
      id: 4,
      title: 'Count Vowels',
      difficulty: 'Medium',
      description: 'Write a function that counts the number of vowels (a, e, i, o, u) in a given string.',
      examples: [
        { input: '"hello"', output: '2' },
        { input: '"programming"', output: '3' },
      ],
      testCases: [
        { input: 'hello', expectedOutput: '2' },
        { input: 'programming', expectedOutput: '3' },
        { input: 'aeiou', expectedOutput: '5' },
      ],
      starterCode: '# Read string from input\ntext = input()\n\n# Write your code here\nvowel_count = 0  # Count vowels\n\nprint(vowel_count)'
    },
    {
      id: 5,
      title: 'Palindrome Check',
      difficulty: 'Medium',
      description: 'Write a function that checks if a given string is a palindrome (reads the same forwards and backwards).',
      examples: [
        { input: '"racecar"', output: 'True' },
        { input: '"hello"', output: 'False' },
      ],
      testCases: [
        { input: 'racecar', expectedOutput: 'True' },
        { input: 'hello', expectedOutput: 'False' },
        { input: 'madam', expectedOutput: 'True' },
      ],
      starterCode: '# Read string from input\ntext = input()\n\n# Write your code here\nis_palindrome = False  # Check palindrome\n\nprint(is_palindrome)'
    },
    {
      id: 6,
      title: 'Fibonacci Sequence',
      difficulty: 'Medium',
      description: 'Write a function that generates the first n numbers in the Fibonacci sequence.',
      examples: [
        { input: 'n = 5', output: '[0, 1, 1, 2, 3]' },
        { input: 'n = 8', output: '[0, 1, 1, 2, 3, 5, 8, 13]' },
      ],
      testCases: [
        { input: '5', expectedOutput: '0 1 1 2 3' },
        { input: '8', expectedOutput: '0 1 1 2 3 5 8 13' },
        { input: '3', expectedOutput: '0 1 1' },
      ],
      starterCode: '# Read n from input\nn = int(input())\n\n# Write your code here\nfib = []  # Generate Fibonacci sequence\n\nprint(" ".join(map(str, fib)))'
    }
  ];

  const cProblems = [
    {
      id: 1,
      title: 'Sum of Two Numbers',
      difficulty: 'Easy',
      description: 'Write a C program that reads two integers and prints their sum.',
      examples: [
        { input: 'a = 5, b = 3', output: '8' },
        { input: 'a = -2, b = 7', output: '5' },
      ],
      testCases: [
        { input: '5\n3', expectedOutput: '8' },
        { input: '-2\n7', expectedOutput: '5' },
        { input: '100\n200', expectedOutput: '300' },
      ],
      starterCode: '#include <stdio.h>\n\nint main() {\n    int a, b;\n    // Read two numbers\n    scanf("%d", &a);\n    scanf("%d", &b);\n    \n    // Write your code here\n    int result = 0;  // Calculate sum\n    \n    printf("%d", result);\n    return 0;\n}'
    },
    {
      id: 2,
      title: 'Reverse a String',
      difficulty: 'Easy',
      description: 'Write a C program that reads a string and prints it in reverse.',
      examples: [
        { input: '"hello"', output: '"olleh"' },
        { input: '"world"', output: '"dlrow"' },
      ],
      testCases: [
        { input: 'hello', expectedOutput: 'olleh' },
        { input: 'world', expectedOutput: 'dlrow' },
        { input: 'abcdef', expectedOutput: 'fedcba' },
      ],
      starterCode: '#include <stdio.h>\n#include <string.h>\n\nint main() {\n    char str[100];\n    // Read string from input\n    scanf("%s", str);\n    \n    // Write your code here\n    // Reverse the string\n    \n    printf("%s", str);\n    return 0;\n}'
    },
    {
      id: 3,
      title: 'Find Maximum Number',
      difficulty: 'Easy',
      description: 'Write a C program that finds the maximum number from an array of integers.',
      examples: [
        { input: 'n=5: [1, 5, 3, 9, 2]', output: '9' },
        { input: 'n=4: [-5, -2, -10, -1]', output: '-1' },
      ],
      testCases: [
        { input: '5\n1 5 3 9 2', expectedOutput: '9' },
        { input: '4\n-5 -2 -10 -1', expectedOutput: '-1' },
        { input: '4\n100 50 200 75', expectedOutput: '200' },
      ],
      starterCode: '#include <stdio.h>\n\nint main() {\n    int n, i;\n    scanf("%d", &n);\n    int arr[n];\n    \n    for(i = 0; i < n; i++) {\n        scanf("%d", &arr[i]);\n    }\n    \n    // Write your code here\n    int max = arr[0];  // Find maximum\n    \n    printf("%d", max);\n    return 0;\n}'
    },
    {
      id: 4,
      title: 'Count Vowels',
      difficulty: 'Medium',
      description: 'Write a C program that counts the number of vowels (a, e, i, o, u) in a string.',
      examples: [
        { input: '"hello"', output: '2' },
        { input: '"programming"', output: '3' },
      ],
      testCases: [
        { input: 'hello', expectedOutput: '2' },
        { input: 'programming', expectedOutput: '3' },
        { input: 'aeiou', expectedOutput: '5' },
      ],
      starterCode: '#include <stdio.h>\n#include <string.h>\n#include <ctype.h>\n\nint main() {\n    char str[100];\n    scanf("%s", str);\n    \n    // Write your code here\n    int count = 0;  // Count vowels\n    \n    printf("%d", count);\n    return 0;\n}'
    },
    {
      id: 5,
      title: 'Palindrome Check',
      difficulty: 'Medium',
      description: 'Write a C program that checks if a string is a palindrome.',
      examples: [
        { input: '"racecar"', output: '1' },
        { input: '"hello"', output: '0' },
      ],
      testCases: [
        { input: 'racecar', expectedOutput: '1' },
        { input: 'hello', expectedOutput: '0' },
        { input: 'madam', expectedOutput: '1' },
      ],
      starterCode: '#include <stdio.h>\n#include <string.h>\n\nint main() {\n    char str[100];\n    scanf("%s", str);\n    \n    // Write your code here\n    int isPalindrome = 0;  // Check palindrome (1 for true, 0 for false)\n    \n    printf("%d", isPalindrome);\n    return 0;\n}'
    },
    {
      id: 6,
      title: 'Factorial Calculator',
      difficulty: 'Medium',
      description: 'Write a C program that calculates the factorial of a number.',
      examples: [
        { input: 'n = 5', output: '120' },
        { input: 'n = 3', output: '6' },
      ],
      testCases: [
        { input: '5', expectedOutput: '120' },
        { input: '3', expectedOutput: '6' },
        { input: '4', expectedOutput: '24' },
      ],
      starterCode: '#include <stdio.h>\n\nint main() {\n    int n;\n    scanf("%d", &n);\n    \n    // Write your code here\n    long long factorial = 1;  // Calculate factorial\n    \n    printf("%lld", factorial);\n    return 0;\n}'
    }
  ];

  const problems = language === 'c' ? cProblems : pythonProblems;
  const currentProblem = problems[currentProblemIndex];
  
  // Initialize code with the first problem's starter code
  React.useEffect(() => {
    setCode(problems[0].starterCode);
  }, [language, problems]);

  const runCode = async () => {
    setIsRunning(true);
    setOutput('Running code...');
    setTestResults(null);

    try {
      // Encode code in base64
      const encodedCode = btoa(unescape(encodeURIComponent(code)));
      
      // Use Flask backend - select endpoint based on language
      const endpoint = language === 'c' 
        ? 'http://localhost:5000/api/student/execute-c-code'
        : 'http://localhost:5000/api/student/execute-code';
        
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          source_code: encodedCode,
          language_id: language === 'c' ? 50 : 71,
          stdin: btoa(''),
          base64_encoded: true,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      
      // Log the full response for debugging
      console.log('Code Execution Response:', result);
      
      // Check for internal errors
      if (result.status && result.status.id === 13) {
        let errorMsg = '⚠️ Server Error\n\n';
        if (result.message) {
          try {
            const decodedMsg = atob(result.message);
            errorMsg += 'Error: ' + decodedMsg + '\n\n';
          } catch (e) {
            errorMsg += 'Error: ' + result.message + '\n\n';
          }
        }
        setOutput(errorMsg);
        return;
      }
      
      // Check status
      if (result.status && result.status.id === 3) {
        // Status 3 = Accepted (successful execution)
        if (result.stdout) {
          setOutput(atob(result.stdout));
        } else {
          setOutput('(No output - program ran successfully but printed nothing)');
        }
      } else if (result.status && result.status.id === 5) {
        // Time Limit Exceeded
        setOutput('⏱️ Time Limit Exceeded (5 seconds)\n\nYour code took too long to execute.');
      } else if (result.status && result.status.id === 11) {
        // Runtime Error
        if (result.stderr) {
          setOutput('Runtime Error:\n' + atob(result.stderr));
        } else {
          setOutput('Runtime Error: Unknown error occurred');
        }
      } else if (result.stdout) {
        setOutput(atob(result.stdout));
      } else if (result.stderr) {
        setOutput('Error:\n' + atob(result.stderr));
      } else if (result.compile_output) {
        setOutput('Compilation Error:\n' + atob(result.compile_output));
      } else if (result.message) {
        let msg = result.message;
        try {
          msg = atob(result.message);
        } catch (e) {
          // Not base64 encoded
        }
        setOutput('Error: ' + msg);
      } else {
        setOutput('No output');
      }
    } catch (error) {
      let errorMsg = '❌ Cannot connect to code execution server\n\n';
      errorMsg += 'Make sure your Flask backend is running on localhost:5000\n\n';
      errorMsg += 'To start the backend:\n';
      errorMsg += '1. Open a terminal in: ProeduVate-main\\backend\n';
      errorMsg += '2. Run: python run.py\n\n';
      errorMsg += 'Error details: ' + error.message;
      setOutput(errorMsg);
      console.error('Error running code:', error);
    } finally {
      setIsRunning(false);
    }
  };

  const runTestCases = async () => {
    setIsRunning(true);
    setOutput('Running test cases...');
    setTestResults([]);

    const results = [];
    
    for (let i = 0; i < currentProblem.testCases.length; i++) {
      const testCase = currentProblem.testCases[i];
      
      try {
        const encodedCode = btoa(unescape(encodeURIComponent(code)));
        const encodedInput = btoa(testCase.input);
        
        // Use Flask backend - select endpoint based on language
        const endpoint = language === 'c' 
          ? 'http://localhost:5000/api/student/execute-c-code'
          : 'http://localhost:5000/api/student/execute-code';
          
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            source_code: encodedCode,
            language_id: language === 'c' ? 50 : 71,
            stdin: encodedInput,
            base64_encoded: true,
          }),
        });

        const result = await response.json();
        
        console.log(`Test Case ${i + 1} Response:`, result);
        
        let actualOutput = '';
        let passed = false;
        let error = null;

        if (result.status && result.status.id === 3) {
          // Status 3 = Accepted
          if (result.stdout) {
            actualOutput = atob(result.stdout).trim();
            passed = actualOutput === testCase.expectedOutput;
          } else {
            actualOutput = '(empty)';
          }
        } else if (result.status && result.status.id === 5) {
          error = 'Time Limit Exceeded';
        } else if (result.status && result.status.id === 11) {
          if (result.stderr) {
            error = atob(result.stderr);
          } else {
            error = 'Runtime Error';
          }
        } else if (result.stdout) {
          actualOutput = atob(result.stdout).trim();
          passed = actualOutput === testCase.expectedOutput;
        } else if (result.stderr) {
          error = atob(result.stderr);
        } else if (result.compile_output) {
          error = atob(result.compile_output);
        } else if (result.message) {
          error = result.message;
        }

        results.push({
          testCase: i + 1,
          input: testCase.input,
          expectedOutput: testCase.expectedOutput,
          actualOutput: actualOutput || 'No output',
          passed: passed,
          error: error,
        });
      } catch (error) {
        results.push({
          testCase: i + 1,
          input: testCase.input,
          expectedOutput: testCase.expectedOutput,
          actualOutput: 'Error',
          passed: false,
          error: 'Failed to run test case',
        });
      }
    }

    setTestResults(results);
    
    const passedCount = results.filter(r => r.passed).length;
    setOutput(`Test Results: ${passedCount}/${results.length} test cases passed`);
    setIsRunning(false);
  };

  const resetCode = () => {
    setCode(currentProblem.starterCode);
    setOutput('');
    setTestResults(null);
  };

  const nextProblem = () => {
    if (currentProblemIndex < problems.length - 1) {
      setCurrentProblemIndex(currentProblemIndex + 1);
      setCode(problems[currentProblemIndex + 1].starterCode);
      setOutput('');
      setTestResults(null);
    }
  };

  const previousProblem = () => {
    if (currentProblemIndex > 0) {
      setCurrentProblemIndex(currentProblemIndex - 1);
      setCode(problems[currentProblemIndex - 1].starterCode);
      setOutput('');
      setTestResults(null);
    }
  };

  const getDifficultyColor = (difficulty) => {
    switch (difficulty.toLowerCase()) {
      case 'easy':
        return 'text-green-600 bg-green-100';
      case 'medium':
        return 'text-yellow-600 bg-yellow-100';
      case 'hard':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-7xl h-[90vh] flex flex-col">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-6 rounded-t-xl">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <Code size={32} />
              <div>
                <h2 className="text-2xl font-bold">{language === 'c' ? 'C' : 'Python'} Coding Practice</h2>
                <p className="text-blue-100 text-sm">Problem {currentProblemIndex + 1} of {problems.length}</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:bg-white hover:bg-opacity-20 px-4 py-2 rounded-lg transition-colors"
            >
              ✕ Close
            </button>
          </div>

          {/* Problem Navigation */}
          <div className="flex items-center gap-2">
            <button
              onClick={previousProblem}
              disabled={currentProblemIndex === 0}
              className="bg-white bg-opacity-20 hover:bg-opacity-30 px-3 py-1 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              ← Previous
            </button>
            <div className="flex-1 overflow-x-auto flex gap-2">
              {problems.map((problem, index) => (
                <button
                  key={problem.id}
                  onClick={() => {
                    setCurrentProblemIndex(index);
                    setCode(problem.starterCode);
                    setOutput('');
                    setTestResults(null);
                  }}
                  className={`px-3 py-1 rounded text-sm whitespace-nowrap transition-colors ${
                    index === currentProblemIndex
                      ? 'bg-white text-blue-600 font-semibold'
                      : 'bg-white bg-opacity-20 hover:bg-opacity-30'
                  }`}
                >
                  {index + 1}
                </button>
              ))}
            </div>
            <button
              onClick={nextProblem}
              disabled={currentProblemIndex === problems.length - 1}
              className="bg-white bg-opacity-20 hover:bg-opacity-30 px-3 py-1 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Next →
            </button>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Left Panel - Problem Description */}
          <div className="w-1/3 border-r border-gray-700 overflow-y-auto p-6" style={{ backgroundColor: '#252526' }}>
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-xl font-bold text-gray-100">{currentProblem.title}</h3>
                <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getDifficultyColor(currentProblem.difficulty)}`}>
                  {currentProblem.difficulty}
                </span>
              </div>
              <p className="text-gray-300 leading-relaxed">{currentProblem.description}</p>
            </div>

            <div className="mb-4">
              <h4 className="font-semibold text-gray-100 mb-2">Examples:</h4>
              {currentProblem.examples.map((example, index) => (
                <div key={index} className="bg-gray-800 p-3 rounded-lg mb-2 border border-gray-700">
                  <div className="text-sm">
                    <div className="text-gray-400">Input: <span className="font-mono text-blue-300">{example.input}</span></div>
                    <div className="text-gray-400">Output: <span className="font-mono text-green-300">{example.output}</span></div>
                  </div>
                </div>
              ))}
            </div>

            <div>
              <h4 className="font-semibold text-gray-100 mb-2">Test Cases:</h4>
              <p className="text-sm text-gray-400 mb-2">Your code will be tested against {currentProblem.testCases.length} test cases.</p>
              {testResults && (
                <div className="space-y-2">
                  {testResults.map((result, index) => (
                    <div
                      key={index}
                      className={`p-3 rounded-lg border-2 ${
                        result.passed
                          ? 'bg-green-900 bg-opacity-30 border-green-600'
                          : 'bg-red-900 bg-opacity-30 border-red-600'
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        {result.passed ? (
                          <CheckCircle className="text-green-400" size={16} />
                        ) : (
                          <XCircle className="text-red-400" size={16} />
                        )}
                        <span className="font-semibold text-sm text-gray-200">Test Case {result.testCase}</span>
                      </div>
                      <div className="text-xs space-y-1">
                        <div className="text-gray-300">Input: <span className="font-mono text-blue-300">{result.input}</span></div>
                        <div className="text-gray-300">Expected: <span className="font-mono text-green-300">{result.expectedOutput}</span></div>
                        <div className="text-gray-300">Got: <span className="font-mono text-yellow-300">{result.actualOutput}</span></div>
                        {result.error && (
                          <div className="text-red-400">Error: {result.error}</div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right Panel - Code Editor and Output */}
          <div className="flex-1 flex flex-col" style={{ backgroundColor: '#1e1e1e' }}>
            {/* Code Editor */}
            <div className="flex-1 flex flex-col p-4">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-semibold text-gray-200">Code Editor</h4>
                <div className="flex gap-2">
                  <button
                    onClick={resetCode}
                    className="flex items-center gap-1 text-gray-300 hover:text-white px-3 py-1 rounded hover:bg-gray-700 transition-colors text-sm"
                  >
                    <RotateCcw size={16} />
                    Reset
                  </button>
                  <button
                    onClick={runCode}
                    disabled={isRunning}
                    className="flex items-center gap-1 bg-green-500 hover:bg-green-600 text-white px-4 py-1 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
                  >
                    <Play size={16} />
                    Run Code
                  </button>
                  <button
                    onClick={runTestCases}
                    disabled={isRunning}
                    className="flex items-center gap-1 bg-blue-500 hover:bg-blue-600 text-white px-4 py-1 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
                  >
                    <Trophy size={16} />
                    Submit
                  </button>
                </div>
              </div>
              <div className="flex-1 w-full border-2 border-gray-700 rounded-lg overflow-hidden" style={{ backgroundColor: '#1e1e1e' }}>
                <CodeEditor
                  value={code}
                  language="python"
                  placeholder="Write your Python code here..."
                  onChange={(evn) => setCode(evn.target.value)}
                  padding={16}
                  style={{
                    fontFamily: '"Fira Code", "Consolas", "Monaco", "Courier New", monospace',
                    fontSize: 14,
                    backgroundColor: '#1e1e1e',
                    minHeight: '100%',
                    outline: 'none',
                  }}
                  data-color-mode="dark"
                />
              </div>
            </div>

            {/* Output Panel */}
            <div className="border-t-2 border-gray-700 p-4" style={{ backgroundColor: '#252526' }}>
              <div className="flex items-center gap-2 mb-2">
                <h4 className="font-semibold text-gray-200">Output</h4>
                {isRunning && <Clock className="animate-spin text-blue-400" size={16} />}
              </div>
              <pre className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm h-32 overflow-y-auto whitespace-pre-wrap">
                {output || 'Output will appear here...'}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CodingInterface;
