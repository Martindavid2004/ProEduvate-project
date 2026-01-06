import React, { useState, useEffect } from 'react';
import { Play, RotateCcw, CheckCircle, XCircle, Clock, Trophy, Code, Terminal, Keyboard } from 'lucide-react';
import CodeEditor from '@uiw/react-textarea-code-editor';

const CodingInterface = ({ onClose }) => {
  const [code, setCode] = useState('');
  const [output, setOutput] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [testResults, setTestResults] = useState(null);
  const [currentProblemIndex, setCurrentProblemIndex] = useState(0);
  const [customInput, setCustomInput] = useState('');
  const [activeConsoleTab, setActiveConsoleTab] = useState('input');
  const [isProblemVisible, setIsProblemVisible] = useState(true);
  
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
      starterCode: '# Read two numbers from input\na = int(input())\nb = int(input())\n\n# Write your code here\nresult = a + b  # Calculate sum\n\nprint(result)'
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

  const currentProblem = pythonProblems[currentProblemIndex];
  
  useEffect(() => {
    setCode(pythonProblems[0].starterCode);
  }, []);

  const runCode = async () => {
    setIsRunning(true);
    setActiveConsoleTab('output');
    setOutput('Running code...');
    setTestResults(null);

    try {
      const encodedCode = btoa(unescape(encodeURIComponent(code)));
      const encodedInput = customInput ? btoa(customInput) : btoa('');
      
      const response = await fetch('http://localhost:5000/api/student/execute-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_code: encodedCode,
          language_id: 71,
          stdin: encodedInput,
          base64_encoded: true,
        }),
      });

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

      const result = await response.json();
      
      if (result.status && result.status.id === 13) {
        setOutput('⚠️ Server Error\n\n' + (result.message || ''));
        return;
      }
      
      if (result.status && result.status.id === 3) {
        setOutput(result.stdout ? atob(result.stdout) : '');
      } else if (result.status && result.status.id === 5) {
        setOutput('⏱️ Time Limit Exceeded (5 seconds)\n\nYour code took too long to execute.');
      } else if (result.status && result.status.id === 11) {
        if (result.stderr) {
          const errorMsg = atob(result.stderr);
          if (errorMsg.includes('EOFError') || errorMsg.includes('EOF when reading a line')) {
            setOutput('❌ Input Required\n\nYour program is trying to read input using input() but no input was provided.\n\n💡 How to fix:\n1. Click the "Input" tab below\n2. Enter your input values (one per line)\n3. Click "Run Code" again');
            setActiveConsoleTab('input');
          } else if (errorMsg.includes('ValueError: invalid literal for int()')) {
            setOutput('❌ Invalid Input Type\n\nYour program expected a number but received text instead.\n\n💡 How to fix:\n1. Click the "Input" tab below\n2. Make sure you enter numbers (e.g., 5 and 3)\n3. Each input should be on a new line\n4. Click "Run Code" again\n\n' + errorMsg);
            setActiveConsoleTab('input');
          } else {
            setOutput(`Traceback (most recent call last):\n${errorMsg}`);
          }
        } else {
          setOutput('Runtime Error: Unknown error occurred');
        }
      } else if (result.stdout) {
        setOutput(atob(result.stdout));
      } else if (result.stderr) {
        setOutput(`Error:\n${atob(result.stderr)}`);
      } else {
        setOutput('(No output)');
      }
    } catch (error) {
      setOutput(`❌ Error: ${error.message}\nCheck if backend is running.`);
    } finally {
      setIsRunning(false);
    }
  };

  const runTestCases = async () => {
    setIsRunning(true);
    setActiveConsoleTab('output');
    setOutput('Running test cases...');
    setTestResults([]);

    const results = [];
    
    for (let i = 0; i < currentProblem.testCases.length; i++) {
      const testCase = currentProblem.testCases[i];
      
      try {
        const encodedCode = btoa(unescape(encodeURIComponent(code)));
        const encodedInput = btoa(testCase.input);
        
        const response = await fetch('http://localhost:5000/api/student/execute-code', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            source_code: encodedCode,
            language_id: 71,
            stdin: encodedInput,
            base64_encoded: true,
          }),
        });

        const result = await response.json();
        let actualOutput = '';
        let passed = false;
        let error = null;

        if (result.status && result.status.id === 3 && result.stdout) {
          actualOutput = atob(result.stdout).trim();
          passed = actualOutput === testCase.expectedOutput;
        } else if (result.stderr) {
          error = atob(result.stderr);
        }

        results.push({
          testCase: i + 1,
          input: testCase.input,
          expectedOutput: testCase.expectedOutput,
          actualOutput: actualOutput === '' && result.status && result.status.id === 3 ? '(empty)' : (actualOutput || 'No output'),
          passed,
          error,
        });
      } catch (error) {
        results.push({ testCase: i + 1, passed: false, error: 'Network Error' });
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
    if (currentProblemIndex < pythonProblems.length - 1) {
      setCurrentProblemIndex(currentProblemIndex + 1);
      setCode(pythonProblems[currentProblemIndex + 1].starterCode);
      setOutput('');
      setTestResults(null);
    }
  };

  const previousProblem = () => {
    if (currentProblemIndex > 0) {
      setCurrentProblemIndex(currentProblemIndex - 1);
      setCode(pythonProblems[currentProblemIndex - 1].starterCode);
      setOutput('');
      setTestResults(null);
    }
  };

  const getDifficultyColor = (difficulty) => {
    switch (difficulty.toLowerCase()) {
      case 'easy': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'hard': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className="min-h-screen bg-white flex flex-col">
      <div className="bg-white w-full h-screen flex flex-col">
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-3 sm:p-6">
          <div className="flex items-center justify-between mb-2 sm:mb-4">
            <div className="flex items-center gap-2 sm:gap-3">
              <Code size={24} className="sm:w-8 sm:h-8" />
              <div>
                <h2 className="text-lg sm:text-2xl font-bold">Python Coding Practice</h2>
                <p className="text-blue-100 text-xs sm:text-sm">Problem {currentProblemIndex + 1} of {pythonProblems.length}</p>
              </div>
            </div>
            <button onClick={onClose} className="text-white hover:bg-white hover:bg-opacity-20 px-2 sm:px-4 py-1 sm:py-2 rounded-lg transition-colors text-sm sm:text-base">
              ✕ Close
            </button>
          </div>

          <div className="flex items-center gap-1 sm:gap-2">
            <button onClick={previousProblem} disabled={currentProblemIndex === 0} className="bg-white bg-opacity-20 hover:bg-opacity-30 px-2 sm:px-3 py-1 rounded text-xs sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
              ←
            </button>
            <div className="flex-1 overflow-x-auto flex gap-1 sm:gap-2">
              {pythonProblems.map((problem, index) => (
                <button
                  key={problem.id}
                  onClick={() => {
                    setCurrentProblemIndex(index);
                    setCode(problem.starterCode);
                    setOutput('');
                    setTestResults(null);
                  }}
                  className={`px-2 sm:px-3 py-1 rounded text-xs sm:text-sm whitespace-nowrap transition-colors ${
                    index === currentProblemIndex ? 'bg-white text-blue-600 font-semibold' : 'bg-white bg-opacity-20 hover:bg-opacity-30'
                  }`}
                >
                  {index + 1}
                </button>
              ))}
            </div>
            <button onClick={nextProblem} disabled={currentProblemIndex === pythonProblems.length - 1} className="bg-white bg-opacity-20 hover:bg-opacity-30 px-2 sm:px-3 py-1 rounded text-xs sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
              →
            </button>
          </div>
        </div>

        <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
          {/* Problem Description Panel - Collapsible on Mobile */}
          <div 
            className={`${isProblemVisible ? 'block' : 'hidden lg:block'} w-full lg:w-1/3 border-b lg:border-b-0 lg:border-r border-gray-700 overflow-y-auto p-3 sm:p-6`} 
            style={{ backgroundColor: '#252526' }}>
            <div className="mb-3 sm:mb-4">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-base sm:text-xl font-bold text-gray-100">{currentProblem.title}</h3>
                <div className="flex items-center gap-2">
                  <span className={`px-2 sm:px-3 py-0.5 sm:py-1 rounded-full text-xs font-semibold ${getDifficultyColor(currentProblem.difficulty)}`}>
                    {currentProblem.difficulty}
                  </span>
                  <button 
                    onClick={() => setIsProblemVisible(!isProblemVisible)}
                    className="lg:hidden text-gray-400 hover:text-white px-2 py-1 rounded text-xs"
                  >
                    {isProblemVisible ? '✕' : ''}
                  </button>
                </div>
              </div>
              <p className="text-gray-300 leading-relaxed text-xs sm:text-base">{currentProblem.description}</p>
            </div>

            <div className="mb-3 sm:mb-4">
              <h4 className="font-semibold text-gray-100 mb-2 text-sm sm:text-base">Examples:</h4>
              {currentProblem.examples.map((example, index) => (
                <div key={index} className="bg-gray-800 p-2 sm:p-3 rounded-lg mb-2 border border-gray-700">
                  <div className="text-xs sm:text-sm">
                    <div className="text-gray-400 break-all">Input: <span className="font-mono text-blue-300">{example.input}</span></div>
                    <div className="text-gray-400 break-all">Output: <span className="font-mono text-green-300">{example.output}</span></div>
                  </div>
                </div>
              ))}
            </div>

            <div>
              <h4 className="font-semibold text-gray-100 mb-2 text-sm sm:text-base">Test Cases:</h4>
              {testResults && (
                <div className="space-y-2">
                  {testResults.map((result, index) => (
                    <div key={index} className={`p-2 sm:p-3 rounded-lg border-2 ${result.passed ? 'bg-green-900 bg-opacity-30 border-green-600' : 'bg-red-900 bg-opacity-30 border-red-600'}`}>
                      <div className="flex items-center gap-2 mb-1">
                        {result.passed ? <CheckCircle className="text-green-400" size={14} /> : <XCircle className="text-red-400" size={14} />}
                        <span className="font-semibold text-xs sm:text-sm text-gray-200">Test Case {result.testCase}</span>
                      </div>
                      <div className="text-xs space-y-1">
                        <div className="text-gray-300 break-all">Input: <span className="font-mono text-blue-300">{result.input}</span></div>
                        <div className="text-gray-300 break-all">Expected: <span className="font-mono text-green-300">{result.expectedOutput}</span></div>
                        <div className="text-gray-300 break-all">Got: <span className="font-mono text-yellow-300">{result.actualOutput}</span></div>
                        {result.error && <div className="text-red-400 break-all">Error: {result.error}</div>}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Code Editor and Console Panel */}
          <div className="flex-1 flex flex-col" style={{ backgroundColor: '#1e1e1e' }}>
            {/* Toggle Problem Button (Mobile Only) */}
            {!isProblemVisible && (
              <button 
                onClick={() => setIsProblemVisible(true)}
                className="lg:hidden bg-blue-600 text-white px-3 py-2 m-2 rounded text-xs font-medium hover:bg-blue-700 transition-colors"
              >
                📋 Show Problem
              </button>
            )}
            
            <div className="flex-1 flex flex-col p-2 sm:p-4">
              <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
                <h4 className="font-semibold text-gray-200 text-sm sm:text-base">Code Editor</h4>
                <div className="flex gap-1 sm:gap-2">
                  <button onClick={resetCode} className="flex items-center gap-1 text-gray-300 hover:text-white px-2 sm:px-3 py-1 rounded hover:bg-gray-700 transition-colors text-xs sm:text-sm">
                    <RotateCcw size={14} className="sm:w-4 sm:h-4" /> <span className="hidden sm:inline">Reset</span>
                  </button>
                  <button onClick={runCode} disabled={isRunning} className="flex items-center gap-1 bg-green-500 hover:bg-green-600 text-white px-2 sm:px-4 py-1 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-xs sm:text-sm font-medium">
                    <Play size={14} className="sm:w-4 sm:h-4" /> Run
                  </button>
                  <button onClick={runTestCases} disabled={isRunning} className="flex items-center gap-1 bg-blue-500 hover:bg-blue-600 text-white px-2 sm:px-4 py-1 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-xs sm:text-sm font-medium">
                    <Trophy size={14} className="sm:w-4 sm:h-4" /> Submit
                  </button>
                </div>
              </div>
              <div className="flex-1 w-full border-2 border-gray-700 rounded-lg overflow-hidden" style={{ backgroundColor: '#1e1e1e', minHeight: '200px' }}>
                <CodeEditor
                  value={code}
                  language="python"
                  placeholder="Write your Python code here..."
                  onChange={(evn) => setCode(evn.target.value)}
                  padding={12}
                  style={{
                    fontFamily: '"Fira Code", "Consolas", "Monaco", "Courier New", monospace',
                    fontSize: window.innerWidth < 640 ? 12 : 14,
                    backgroundColor: '#1e1e1e',
                    minHeight: '100%',
                    outline: 'none',
                  }}
                  data-color-mode="dark"
                />
              </div>
            </div>

            <div className="border-t-2 border-gray-700 p-2 sm:p-4" style={{ backgroundColor: '#252526' }}>
              <div className="flex items-center justify-between mb-2">
                <div className="flex gap-2 sm:gap-4">
                    <button 
                        onClick={() => setActiveConsoleTab('input')}
                        className={`flex items-center gap-1 sm:gap-2 px-2 sm:px-3 py-1 rounded-t-lg transition-colors text-xs sm:text-sm font-medium ${
                            activeConsoleTab === 'input' ? 'bg-gray-800 text-white border-t border-x border-gray-600' : 'text-gray-400 hover:text-gray-200'
                        }`}
                    >
                        <Keyboard size={12} className="sm:w-3.5 sm:h-3.5" /> Input
                    </button>
                    <button 
                        onClick={() => setActiveConsoleTab('output')}
                        className={`flex items-center gap-1 sm:gap-2 px-2 sm:px-3 py-1 rounded-t-lg transition-colors text-xs sm:text-sm font-medium ${
                            activeConsoleTab === 'output' ? 'bg-gray-800 text-white border-t border-x border-gray-600' : 'text-gray-400 hover:text-gray-200'
                        }`}
                    >
                        <Terminal size={12} className="sm:w-3.5 sm:h-3.5" /> Output
                    </button>
                </div>
                {isRunning && <div className="flex items-center gap-1 sm:gap-2 text-blue-400 text-xs"><Clock className="animate-spin" size={12} /> <span className="hidden sm:inline">Running...</span></div>}
              </div>

              <div className="bg-gray-900 rounded-b-lg rounded-tr-lg border border-gray-700 overflow-hidden" style={{ height: '150px', display: 'flex', flexDirection: 'column' }}>
                {activeConsoleTab === 'output' ? (
                    <pre className="text-gray-100 p-2 sm:p-4 font-mono text-xs sm:text-sm flex-1 overflow-y-auto whitespace-pre-wrap">
                        {output || <span className="text-gray-500">// Run your code to see output here...</span>}
                    </pre>
                ) : (
                    <textarea 
                        value={customInput}
                        onChange={(e) => setCustomInput(e.target.value)}
                        placeholder="Enter input here (e.g. for split inputs, put each on a new line)"
                        className="w-full h-full bg-gray-900 text-gray-100 p-2 sm:p-4 font-mono text-xs sm:text-sm resize-none focus:outline-none"
                    />
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CodingInterface;
