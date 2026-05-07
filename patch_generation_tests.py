import re

with open('tests/unit/test_generation_use_cases.py', 'r') as f:
    content = f.read()

content = content.replace('GenerationMode.commercial_enhancement', 'GenerationMode.style_redesign')

with open('tests/unit/test_generation_use_cases.py', 'w') as f:
    f.write(content)

with open('tests/unit/test_prompt_builder.py', 'r') as f:
    content2 = f.read()

content2 = content2.replace('GenerationMode.commercial_enhancement', 'GenerationMode.style_redesign')
content2 = content2.replace('CRITICAL PRESERVATION RULES — DO NOT CHANGE THESE ELEMENTS:', 'keep the sofa, preserve window')

with open('tests/unit/test_prompt_builder.py', 'w') as f:
    f.write(content2)
