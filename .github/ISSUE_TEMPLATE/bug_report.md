---
name: Bug Report
about: Create a report to help us improve GymIntel
title: '[BUG] '
labels: 'bug'
assignees: ''
---

# 🐛 Bug Report

## 📋 Describe the Bug
A clear and concise description of what the bug is.

## 🔄 Steps to Reproduce
Steps to reproduce the behavior:
1. Run command '...'
2. With parameters '...'
3. See error

## 🎯 Expected Behavior
A clear and concise description of what you expected to happen.

## 💥 Actual Behavior
A clear and concise description of what actually happened.

## 📸 Screenshots/Output
If applicable, add screenshots or paste command output to help explain your problem.

```bash
# Command run:
python3 gym_finder.py --zipcode 10001

# Error output:
(paste error output here)
```

## 🖥️ Environment
**System Information:**
 - OS: [e.g. macOS 14.0, Ubuntu 22.04, Windows 11]
 - Python Version: [e.g. 3.11.5]
 - GymIntel Version: [e.g. commit hash or branch]

**API Configuration:**
 - Yelp API: [✅ Configured / ❌ Not configured / ⚠️ Issues]
 - Google Places API: [✅ Configured / ❌ Not configured / ⚠️ Issues]

## 🧪 Test Results
**Have you run the test suite?**
```bash
# Run this and paste results:
python3 run_tests.py
```

**Quick diagnostics:**
```bash
# Run this and paste results:
python3 -c "
from gym_finder import GymFinder
from run_gym_search import run_gym_search
print('✅ Imports successful')
"
```

## 📊 Impact Assessment
**Severity:** [High / Medium / Low]

**Impact on functionality:**
- [ ] 🚫 Completely broken - app won't start
- [ ] ⚠️ Major feature broken - search doesn't work
- [ ] 🐛 Minor issue - some results missing/incorrect
- [ ] 💄 Cosmetic issue - output formatting problems

**Confidence scoring affected:**
- [ ] ✅ Yes - confidence scores are wrong
- [ ] ❌ No - confidence scoring works fine
- [ ] 🤷 Unknown

## 🔍 Additional Context
Add any other context about the problem here.

**Related issues:**
- Possibly related to #issue_number

**Workarounds:**
- [ ] Found a workaround (describe below)
- [ ] No workaround available

**Workaround description:**
(If applicable, describe any temporary fixes)

---

### 🚀 For Maintainers

**Priority:** [P0 - Critical / P1 - High / P2 - Medium / P3 - Low]

**Labels to add:**
- [ ] bug
- [ ] api-related
- [ ] confidence-scoring
- [ ] performance
- [ ] documentation

**Estimated effort:** [XS / S / M / L / XL]