import os, sys

data = open(sys.argv[1], 'r').read()
out = open(sys.argv[2], 'w')

func = 'objc_msgSend'

def my_zip(one, two, filltwo):
	l = []
	for i in range(max(len(one), len(two))):
		if i >= len(two): l.append((one[i], filltwo))
		elif i >= len(one): l.append(('', two[i]))
		else: l.append((one[i], two[i]))
	return l 

def make_method(parts):
	if len(parts) < 2: return None
	
	cls = parts[0]
	if cls.find('&OBJC_CLASS___') == 0: cls = cls[14:]
	
	name = parts[1]
	if name[0] != '"' or name[-1] != '"': return None
	name = name[1:-1]
	name_parts = name.split(':')
	if name_parts[-1] == '': name_parts[-1] = None
	
	args = parts[2:] if len(parts) >= 3 else []
	
	build = '[%s' % cls
	if len(name_parts) == 1: 
		build += ' %s' % name_parts[0]
	else:
		for part, arg in my_zip(name_parts, args, 'nil'):
			if part is not None: build += ' %s:%s' % (part, arg) 
	build += ']'
	
	print "[-] Processed method [%s %s]" % (cls, name)
	
	return build

for line in data.split('\n'):
	index = line.find(func)
	if index != -1:
		parts = line[index + len(func) + 1:]
		
		end_index = 0
		deep = 1
		for i, char in enumerate(parts):
			if char == '(': deep += 1
			if char == ')': deep -= 1
			if deep == 0: break
			end_index += 1
			
		parts = parts[:end_index]
		parts = parts.split(', ')
		new = make_method(parts)
		if new is not None:
			line = line[:index] + new + line[index + len(func) + end_index + 2:]
	out.write(line + '\n')
		
		
		