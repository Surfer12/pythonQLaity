import python

from Function f, Call c
where
  f.getName() in [
      "open", "read", "write", // File operations
      "system", "popen", "run", // System commands
      "urlopen", "get", "post" // Network operations
    ] and
  c.getFunc() = f
select c, "Found computer interaction: " + f.getName()
