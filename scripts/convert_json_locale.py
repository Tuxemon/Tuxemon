import json
import sys


def escape(line):
    return line.replace("\n", "\\n")


def main(inpath, outpath):
    with open(inpath) as fp:
        data = json.load(fp)
    with open(outpath, "w") as fp:
        for key, value in data.items():
            fp.write(f'msgid "{key}"\n')
            if isinstance(value, list):
                value[0] = escape(value[0])
                fp.write(f'msgstr "{value[0].strip()}"\n')
                for line in value[1:]:
                    line = escape(line)
                    fp.write(f'"{line.strip()}"\n')
                fp.write("\n")
            elif isinstance(value, str):
                value = escape(value)
                fp.write(f'msgstr "{value.strip()}"\n\n')
            else:
                raise Exception

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
