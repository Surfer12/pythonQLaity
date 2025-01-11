/**
 * @name Computer Interactions
 * @description Finds calls to functions that interact with the computer system
 * @kind problem
 * @problem.severity warning
 * @id python/computer-interactions
 */

import python
import semmle.python.security.dataflow.CommandInjection
import semmle.python.security.dataflow.FileAccess

from Call call, FunctionValue func
where
  func.getScope().getName() in [
      "open", "read", "write", // File operations
      "system", "popen", "run", // System commands
      "urlopen", "get", "post" // Network operations
    ] and
  call.getFunc().pointsTo(func)
select call, "Found computer interaction through function: " + func.getScope().getName()
