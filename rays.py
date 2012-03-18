import os, sys, re, shutil

data = open(sys.argv[1], 'r').read()

if os.path.isdir(sys.argv[2]): shutil.rmtree(sys.argv[2])
os.mkdir(sys.argv[2])

funcs = list(re.split(".*--------------------------------------------------------", data))
hex_rays = funcs.pop()
defs = funcs.pop()
decl = funcs.pop()

print len(funcs)

def format(data):
    # this is ordered on purpose, so don't change it
    funcs = ['j__objc_msgSend', 'objc_msgSend']
    built = ''

    def my_zip(one, two, filltwo):
        ''' no clue what this is for, sorry! '''
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
	    
	    return build
    
    for line in data.split('\n'):
        used = None
        for func in funcs:
            if line.find(func + '(') != -1:
                used = func
                break

        index = -1 if used is None else line.find(used)
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

        built = built + line + '\n'

    b = built
    # remove trailing whitespace
    while b[-1] == '\n':
        b = b[:-1]

    l = b.split('\n')
    r = []
    for n in l:
        if n.find('using guessed type') == -1:
            r.append(n)
    return '\n'.join(r)

class Method(object):
    def __init__(self, d):
        d = d[len("// "):]

        self.cls = d[:d.find(" ")]
        d = d[len(self.cls) + len(" "):]

        self.type = d[0] # + for class, - for instance

        d = d[d.find("(") + len(')'):]
        self.ret = d[:d.find(")")]
        d = d[len(self.ret) + len(")"):]

        parts = []
        while len(d) > 0:
            # params or not
            if d.find(")") != -1:
                p = d[:d.find(")")]
                d = d[len(p) + len(")"):]
                if len(d) > 0 and d[0] == ' ': d = d[1:]
            else:
                p = d
                d = d[len(p):]

            if p.find(":") != -1:
                name = p[:p.find(":")]
                p = p[p.find("(") + len("("):]
                arg = p
            else:
                name = p
                arg = None
            if len(name) > 0 and name[0] == ' ': name = name[1:]

            parts.append((name, arg)) 
        self.parts = parts

    def definition(self):
        r = self.type
        r += " "
        r += '(' + self.ret + ')'
    
        i = 2
        for name, arg in self.parts:
            if i != 2: r += ' '
            if arg is not None:
                r += name + ":("
                r += arg if arg != "char" else "BOOL"
                r += ")a" + str(i) # match hex-rays
            else:
                r += name
            i += 1

        return r

    def formatted(self): 
        b = format(self.body)
        return b

methods = []
ignored = []

for func in funcs[3:]:
    lines = func.split("\n")
    if len(lines) <= 1:
        ignored.append(func)
        continue

    line = lines[1]
    if line[:2] == '//': # find objc methods
        m = Method(line)
        m.body = '\n'.join(lines[3:]) # ignore first two lines
        methods.append(m)

    ignored.append(func)
    continue

# write out

out = open(sys.argv[2] + "/" + "main.m", 'w')

for block in ignored:
    out.write(format(block) + '\n')

out.write("\n\n")

import itertools

ms = sorted(methods, key=lambda x: x.cls)

for cls, m in itertools.groupby(ms, lambda x: x.cls):
    fn = cls
    if fn.find('(') != -1:
        fn = fn[:fn.find('(')] + '+' + fn[fn.find('(') + len('('):fn.find(')')]

    out = open(sys.argv[2] + "/" + fn + ".m", 'w')

    out.write('#import "' + cls + '.h"\n')
    out.write('\n@implementation ' + cls + '\n')

    for method in m:
        out.write('\n')
        out.write(method.definition())
        out.write(' ')
        out.write(method.formatted())
        out.write('\n')

    out.write('\n@end\n\n')



    








