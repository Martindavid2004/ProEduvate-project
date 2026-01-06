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
  const [activeConsoleTab, setActiveConsoleTab] = useState('input'); // 'input' or 'output'
  
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
  
  // Initialize code with the first problem's starter code
  useEffect(() => {
    setCode(pythonProblems[0].starterCode);
  }, []);

  const runCode = async () => {
    setIsRunning(true);
    setActiveConsoleTab('output'); // Switch to output tab when running
    setOutput('Running code...');
    setTestResults(null);

    try {
      const encodedCode = btoa(unescape(encodeURIComponent(code)));
      const encodedInput = customInput ? btoa(customInput) : btoa('');
      
      const endpoint = 'http://localhost:5000/api/student/execute-code';
        
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          source_code: encodedCode,
          language_id: 71,
          stdin: encodedInput,
          base64_encoded: true,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      console.log('Code Execution Response:', result);
      
      if (result.status && result.status.id === 13) {
        let errorMsg = '⚠️ Server Error\n\n';
        if (result.message) errorMsg += 'Error: ' + result.message;
        setOutput(errorMsg);
        return;
      }
      
      // Handle Success and Errors
      if (result.status && result.status.id === 3) {
        if (result.stdout) {
          const outputText = atob(result.stdout);
          setOutput(outputText);
        } else {
          setOutput('');
        }
      } else if (result.status && result.status.id === 5) {
        setOutput('⏱️ Time Limit Exceeded (5 seconds)\n\nYour code took too long to execute.');
      } else if (result.status && result.status.id === 11) {
         if (result.stderr) {
            const error = atob(result.stderr);
            setOutput(`Traceback (most recent call last):\n${error}`);
         } else {
            setOutput('Runtime Error: Unknown error occurred');
         }
      } else if (result.stdout) {
        setOutput(atob(result.stdout));
      } else if (result.stderr) {
        setOutput(`Error:\n${atob(result.stderr)}`);
      } else if (result.compile_output) {
        setOutput(`Compilation Error:\n${atob(result.compile_output)}`);
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
        const endpoint = 'http://localhost:5000/api/student/execute-code';
        const response = await fetch(endpoint, {
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

        if (result.status && result.status.id === 3) {
           if(result.stdout) {
             actualOutput = atob(result.stdout).trim();
             passed = actualOutput === testCase.expectedOutput;
           }
        } else if (result.stderr) {
           error = atob(result.stderr);
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
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-7xl h-[90vh] flex flex-col">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-6 rounded-t-xl">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <Code size={32} />
              <div>
                <h2 className="text-2xl font-bold">Python Coding Practice</h2>
                <p className="text-blue-100 text-sm">Problem {currentProblemIndex + 1} of {pythonProblems.length}</p>
              </div>
            </div>
            <button onClick={onClose} className="text-white hover:bg-white hover:bg-opacity-20 px-4 py-2 rounded-lg transition-colors">
              ✕ Close
            </button>
          </div>

          {/* Problem Navigation */}
          <div className="flex items-center gap-2">
            <button onClick={previousProblem} disabled={currentProblemIndex === 0} className="bg-white bg-opacity-20 hover:bg-opacity-30 px-3 py-1 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
              ← Previous
            </button>
            <div className="flex-1 overflow-x-auto flex gap-2">
              {pythonProblems.map((problem, index) => (
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
              disabled={currentProblemIndex === pythonProblems.length - 1}
              className="bg-white bg-opacity-20 hover:bg-opacity-30 px-3 py-1 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            > ? 'bg-white text-blue-600 font-semibold'
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Left Panel - Problem Description */}
          <div clas onClick={nextProblem} disabled={currentProblemIndex === pythonProblems.length - 1} className="bg-white bg-opacity-20 hover:bg-opacity-30 px-3 py-1 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed transition-colors"    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getDifficultyColor(currentProblem.difficulty)}`}>
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
                        <span className="font-semibold text-sm text-gray-200">Test Case {result.testCase}</span>
                      </div>
                      <div className="text-xs space-y-1">
                        <div className="text-gray-300">Input: <span className="font-mono text-blue-300">{result.input}</span></div>
                         key={index} className={`p-3 rounded-lg border-2 ${result.passed ? 'bg-green-900 bg-opacity-30 border-green-600' : 'bg-red-900 bg-opacity-30 border-red-600'}`}>
                      <div className="flex items-center gap-2 mb-1">
                        {result.passed ? <CheckCircle className="text-green-400" size={16} /> : <XCircle className="text-red-400" size={16} />}
                        <span className="font-semibold text-sm text-gray-200">Test Case {result.testCase}</span>
                      </div>
                      <div className="text-xs space-y-1">
                        <div className="text-gray-300">Input: <span className="font-mono text-blue-300">{result.input}</span></div>
                        <div className="text-gray-300">Expected: <span className="font-mono text-green-300">{result.expectedOutput}</span></div>
                        <div className="text-gray-300">Got: <span className="font-mono text-yellow-300">{result.actualOutput}</span></div>
                        {result.error && <div className="text-red-400">Error: {result.error}</div>Name="flex items-center gap-1 text-gray-300 hover:text-white px-3 py-1 rounded hover:bg-gray-700 transition-colors text-sm"
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
                  padding onClick={resetCode} className="flex items-center gap-1 text-gray-300 hover:text-white px-3 py-1 rounded hover:bg-gray-700 transition-colors text-sm">
                    <RotateCcw size={16} /> Reset
                  </button>
                  <button onClick={runCode} disabled={isRunning} className="flex items-center gap-1 bg-green-500 hover:bg-green-600 text-white px-4 py-1 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium">
                    <Play size={16} /> Run Code
                  </button>
                  <button onClick={runTestCases} disabled={isRunning} className="flex items-center gap-1 bg-blue-500 hover:bg-blue-600 text-white px-4 py-1 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium">
                    <Trophy size={16} />e className="text-gray-100 p-4 font-mono text-sm flex-1 overflow-y-auto whitespace-pre-wrap">
                  {output || '// Console output will appear here...'}
                </pre>
                {/* Input Area - Integrated at bottom like real console */}
                <div className="border-t border-gray-700 p-2" style={{ backgroundColor: '#1a1a1a' }}>
                  <div className="flex items-center gap-2">
                    <span className="text-green-400 font-mono text-sm">{'>'}</span>
                    <input
                      type="text"
                      value={customInput}
                      onChange={(e) => setCustomInput(e.target.value)}
                      placeholder="Enter input values separated by space or newline"
                      className="flex-1 bg-transparent text-gray-300 font-mono text-sm outline-none"
                      style={{ border: 'none' }}
                    />
                  </div>
                </div>
              </div>
              <div className="text-xs text-gray-400 mt-2">
                💡 Tip: For programs using input(), enter values in the console input (separate multiple values with spaces or use Enter key)
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CodingInterface;
Redesigned with Tabs */}
            <div className="border-t-2 border-gray-700 p-4" style={{ backgroundColor: '#252526' }}>
              <div className="flex items-center justify-between mb-2">
                <div className="flex gap-4">
                    <button 
                        onClick={() => setActiveConsoleTab('input')}
                        className={`flex items-center gap-2 px-3 py-1 rounded-t-lg transition-colors text-sm font-medium ${
                            activeConsoleTab === 'input' 
                            ? 'bg-gray-800 text-white border-t border-x border-gray-600' 
                            : 'text-gray-400 hover:text-gray-200'
                        }`}
                    >
                        <Keyboard size={14} /> Input
                    </button>
                    <button 
                        onClick={() => setActiveConsoleTab('output')}
                        className={`flex items-center gap-2 px-3 py-1 rounded-t-lg transition-colors text-sm font-medium ${
                            activeConsoleTab === 'output' 
                            ? 'bg-gray-800 text-white border-t border-x border-gray-600' 
                            : 'text-gray-400 hover:text-gray-200'
                        }`}
                    >
                        <Terminal size={14} /> Output
                    </button>
                </div>
                {isRunning && <div className="flex items-center gap-2 text-blue-400 text-xs"><Clock className="animate-spin" size={14} /> Running...</div>}
              </div>

              <div className="bg-gray-900 rounded-b-lg rounded-tr-lg border border-gray-700 overflow-hidden" style={{ height: '200px', display: 'flex', flexDirection: 'column' }}>
                {activeConsoleTab === 'output' ? (
                    <pre className="text-gray-100 p-4 font-mono text-sm flex-1 overflow-y-auto whitespace-pre-wrap">
                        {output || <span className="text-gray-500">// Run your code to see output here...</span>}
                    </pre>
                ) : (
                    <textarea 
                        value={customInput}
                        onChange={(e) => setCustomInput(e.target.value)}
                        placeholder="Enter input here (e.g. for split inputs, put each on a new line)"
                        className="w-full h-full bg-gray-900 text-gray-100 p-4 font-mono text-sm resize-none focus:outline-none"
                    />
                )}