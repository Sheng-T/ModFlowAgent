path = r"e:\project\agent\deploy\05_pull_dorado_models.sh"
with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()
lines[33] = "    log_warn \"No Dorado SIF found in ${DORADO_IMAGE_DIR}\"\n"
with open(path, "w", encoding="utf-8") as f:
    f.writelines(lines)
for i in range(32,39):
    print(lines[i].rstrip())
