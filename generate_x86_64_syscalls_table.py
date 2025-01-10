import sys
import requests
from bs4 import BeautifulSoup

def get_formatted_filename(filename: str):
    return filename.replace('.', '_').upper()

def main():
    argv = sys.argv

    if len(argv) < 2:
        print("Usage: %s <OUTPUT_H>" % (argv[0]))
        exit(0)

    FILENAME = argv[1]

    # URL to get linux_syscalls_table for x86_64
    URL = "https://blog.rchapman.org/posts/Linux_System_Call_Table_for_x86_64/"

    # Syscall arg registers
    REGISTERS = ["%rdi", "%rsi", "%rdx", "%r10", "%r8", "%r9"]

    response = requests.get(URL)
    response.raise_for_status()
    html = response.text

    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table')

    syscalls = []
    existing_syscalls = set()
    for row in table.find_all('tr')[1:]:
        cols = row.find_all('td')
        if len(cols) < 3:
            continue

        syscall_num = cols[0].get_text(strip=True)
        syscall_name = cols[1].get_text(strip=True)

        if syscall_name in existing_syscalls:
            continue
        existing_syscalls.add(syscall_name)

        arguments: dict = {}
        for i in range(len(REGISTERS)):
            arguments[REGISTERS[i]] = cols[i+2].get_text(strip=True)
        
        formatted_args = []
        for reg, arg in arguments.items():
            if arg:
                formatted_args.append(f"{reg}: {arg.strip()}")
    
        syscalls.append((syscall_num, syscall_name, formatted_args))

    output = []
    output.append("/* The code was generated using resources from https://blog.rchapman.org/posts/Linux_System_Call_Table_for_x86_64/ using the generation script (generate_x86_64_syscalls_table.py) */")
    output.append(f'#if !defined(_{get_formatted_filename(FILENAME)}_LOADED)')
    output.append(f'#define _{get_formatted_filename(FILENAME)}_LOADED')
    output.append("typedef enum SystemCall {")
    for syscall_num, syscall_name, arguments in syscalls:
        enum_name = syscall_name.upper()
        comment = f"// {arguments}" if arguments else "// No arguments"
        output.append(f"    {enum_name} = {syscall_num}, {comment}")
    output.append("} SystemCall;")
    output.append(f'#endif /* _{get_formatted_filename(FILENAME)}_LOADED */')

    with open(FILENAME, "w") as file:
        file.write("\n".join(output))

    print(f"C code with enum generated in '{FILENAME}'")


if __name__ == "__main__":
    main()
