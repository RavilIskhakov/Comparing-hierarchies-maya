<img width="904" height="741" alt="image" src="https://github.com/user-attachments/assets/c8f78479-0a85-4879-a1de-c2b7b4edaa3c" />
Hierarchy Diff for Maya
Небольшой тул, который сравнивает две иерархии в Maya и показывает разницу двумя панелями рядом. Неймспейсы не учитываются, так что неважно, зареференшен один риг или нет, имена нод сравниваются по чистому имени.
Я использую его, чтобы быстро посмотреть, что поменялось между апдейтами ригов: выделяешь старую и новую версию, запускаешь скрипт и сразу видишь, что добавилось, что пропало и где сменился тип ноды.
Как пользоваться
Выдели в сцене ровно два объекта и запусти скрипт. Левая панель это A, правая это B.
Цвета строк:

зелёный: нода совпадает
красный: есть только в A
синий: есть только в B
жёлтый: имя одинаковое, но тип ноды разный

Деревья разворачиваются синхронно. Клик по строке выделяет ноду в сцене. Кнопка "Только различия" прячет всё совпавшее. Внизу строка со статистикой по количеству различий.
Совместимо с PySide2 (Maya 2022-2024) и PySide6 (Maya 2025+).

A small tool that compares two hierarchies in Maya and shows the difference in two panels side by side. Namespaces are ignored, so it does not matter if one rig is referenced and the other is not, nodes are matched by their plain name.
I use it to quickly check what changed between rig updates: pick the old and the new version, run the script, and you immediately see what was added, what is gone and where a node type changed.
Usage
Select exactly two objects in the scene and run the script. The left panel is A, the right one is B.
Row colors:

green: the node matches
red: exists only in A
blue: exists only in B
yellow: same name but a different node type

Both trees expand in sync. Click a row to select that node in the scene. The "Only differences" button hides everything that matches. The status line at the bottom shows how many differences were found.
Works with PySide2 (Maya 2022-2024) and PySide6 (Maya 2025+).
