"""
Визуальное сравнение иерархий в Maya без учёта неймспейсов.
Совместимо с PySide2 (Maya 2022-2024) и PySide6 (Maya 2025+)
"""

import maya.cmds as cmds
import maya.OpenMayaUI as omui

# Автоопределение версии PySide
try:
    from PySide6 import QtWidgets, QtGui, QtCore
    from shiboken6 import wrapInstance
except ImportError:
    from PySide2 import QtWidgets, QtGui, QtCore
    from shiboken2 import wrapInstance


def strip_ns(name):
    return name.split('|')[-1].split(':')[-1]


def get_tree(root):
    if not cmds.objExists(root):
        return None

    root_full = cmds.ls(root, long=True)[0]

    def build(node_full):
        name = strip_ns(node_full)
        node_type = cmds.nodeType(node_full)
        children_full = cmds.listRelatives(node_full, children=True, fullPath=True) or []
        children = {}
        for ch in children_full:
            ch_name = strip_ns(ch)
            key = ch_name
            i = 1
            while key in children:
                key = f"{ch_name}#{i}"
                i += 1
            children[key] = build(ch)
        return {'full': node_full, 'type': node_type, 'name': name, 'children': children}

    return build(root_full)


def maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget)


class HierarchyDiffUI(QtWidgets.QDialog):

    COLOR_MATCH = QtGui.QColor(180, 230, 180)
    COLOR_ONLY_A = QtGui.QColor(255, 180, 180)
    COLOR_ONLY_B = QtGui.QColor(180, 200, 255)
    COLOR_TYPE_DIFF = QtGui.QColor(255, 220, 130)

    def __init__(self, tree_a, tree_b, name_a, name_b, parent=None):
        super().__init__(parent or maya_main_window())
        self.setWindowTitle("Hierarchy Diff (без неймспейсов)")
        self.resize(900, 700)

        self.tree_a = tree_a
        self.tree_b = tree_b
        self.stats = {'match': 0, 'only_a': 0, 'only_b': 0, 'type_diff': 0}

        self._build_ui(name_a, name_b)
        self._populate()
        self._update_stats_label()

    def _build_ui(self, name_a, name_b):
        layout = QtWidgets.QVBoxLayout(self)

        # Легенда
        legend = QtWidgets.QHBoxLayout()
        for color, text in [
            (self.COLOR_MATCH, "совпадает"),
            (self.COLOR_ONLY_A, f"только в A ({name_a})"),
            (self.COLOR_ONLY_B, f"только в B ({name_b})"),
            (self.COLOR_TYPE_DIFF, "разные типы нод"),
        ]:
            swatch = QtWidgets.QLabel("    ")
            swatch.setStyleSheet(
                f"background-color: rgb({color.red()},{color.green()},{color.blue()}); "
                f"border: 1px solid #333;"
            )
            legend.addWidget(swatch)
            legend.addWidget(QtWidgets.QLabel(text))
            legend.addSpacing(15)
        legend.addStretch()
        layout.addLayout(legend)

        # Деревья
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.tree_widget_a = self._make_tree_widget()
        self.tree_widget_b = self._make_tree_widget()
        splitter.addWidget(self._wrap_tree(self.tree_widget_a, f"A: {name_a}"))
        splitter.addWidget(self._wrap_tree(self.tree_widget_b, f"B: {name_b}"))
        splitter.setSizes([450, 450])
        layout.addWidget(splitter)

        self.tree_widget_a.itemExpanded.connect(lambda it: self._sync_expand(it, True))
        self.tree_widget_a.itemCollapsed.connect(lambda it: self._sync_expand(it, False))
        self.tree_widget_b.itemExpanded.connect(lambda it: self._sync_expand(it, True))
        self.tree_widget_b.itemCollapsed.connect(lambda it: self._sync_expand(it, False))
        self.tree_widget_a.itemClicked.connect(self._on_item_clicked)
        self.tree_widget_b.itemClicked.connect(self._on_item_clicked)

        self.stats_label = QtWidgets.QLabel()
        self.stats_label.setStyleSheet("font-weight: bold; padding: 5px;")
        layout.addWidget(self.stats_label)

        btn_layout = QtWidgets.QHBoxLayout()
        btn_expand = QtWidgets.QPushButton("Развернуть всё")
        btn_collapse = QtWidgets.QPushButton("Свернуть всё")
        btn_only_diff = QtWidgets.QPushButton("Только различия")
        btn_show_all = QtWidgets.QPushButton("Показать всё")
        btn_close = QtWidgets.QPushButton("Закрыть")

        btn_expand.clicked.connect(lambda: (self.tree_widget_a.expandAll(), self.tree_widget_b.expandAll()))
        btn_collapse.clicked.connect(lambda: (self.tree_widget_a.collapseAll(), self.tree_widget_b.collapseAll()))
        btn_only_diff.clicked.connect(self._show_only_diff)
        btn_show_all.clicked.connect(self._show_all)
        btn_close.clicked.connect(self.close)

        for b in (btn_expand, btn_collapse, btn_only_diff, btn_show_all):
            btn_layout.addWidget(b)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

    def _make_tree_widget(self):
        tw = QtWidgets.QTreeWidget()
        tw.setHeaderLabels(["Нода", "Тип"])
        tw.setColumnWidth(0, 280)
        tw.setAlternatingRowColors(True)
        return tw

    def _wrap_tree(self, tree, title):
        w = QtWidgets.QWidget()
        v = QtWidgets.QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        lbl = QtWidgets.QLabel(title)
        lbl.setStyleSheet("font-weight: bold; padding: 3px;")
        v.addWidget(lbl)
        v.addWidget(tree)
        return w

    def _populate(self):
        self._fill_pair(
            self.tree_widget_a.invisibleRootItem(),
            self.tree_widget_b.invisibleRootItem(),
            {self.tree_a['name']: self.tree_a} if self.tree_a else {},
            {self.tree_b['name']: self.tree_b} if self.tree_b else {},
        )

    def _fill_pair(self, parent_a, parent_b, children_a, children_b):
        all_keys = []
        seen = set()
        for k in children_a:
            if k not in seen:
                all_keys.append(k)
                seen.add(k)
        for k in children_b:
            if k not in seen:
                all_keys.append(k)
                seen.add(k)

        for key in all_keys:
            node_a = children_a.get(key)
            node_b = children_b.get(key)

            if node_a and node_b:
                if node_a['type'] != node_b['type']:
                    color = self.COLOR_TYPE_DIFF
                    status = 'type_diff'
                else:
                    color = self.COLOR_MATCH
                    status = 'match'
            elif node_a:
                color = self.COLOR_ONLY_A
                status = 'only_a'
            else:
                color = self.COLOR_ONLY_B
                status = 'only_b'

            self.stats[status] += 1

            item_a = QtWidgets.QTreeWidgetItem(parent_a)
            item_b = QtWidgets.QTreeWidgetItem(parent_b)

            if node_a:
                item_a.setText(0, node_a['name'])
                item_a.setText(1, node_a['type'])
                item_a.setData(0, QtCore.Qt.UserRole, node_a['full'])
            else:
                item_a.setText(0, "—")
                item_a.setForeground(0, QtGui.QColor(120, 120, 120))

            if node_b:
                item_b.setText(0, node_b['name'])
                item_b.setText(1, node_b['type'])
                item_b.setData(0, QtCore.Qt.UserRole, node_b['full'])
            else:
                item_b.setText(0, "—")
                item_b.setForeground(0, QtGui.QColor(120, 120, 120))

            for col in (0, 1):
                item_a.setBackground(col, color)
                item_b.setBackground(col, color)

            item_a.setData(0, QtCore.Qt.UserRole + 1, status)
            item_b.setData(0, QtCore.Qt.UserRole + 1, status)

            ch_a = node_a['children'] if node_a else {}
            ch_b = node_b['children'] if node_b else {}
            self._fill_pair(item_a, item_b, ch_a, ch_b)

    def _update_stats_label(self):
        s = self.stats
        total = sum(s.values())
        diff = s['only_a'] + s['only_b'] + s['type_diff']
        verdict = "✅ ИДЕНТИЧНЫ" if diff == 0 else f"❌ РАЗЛИЧИЙ: {diff}"
        self.stats_label.setText(
            f"{verdict}   |   Всего: {total}   |   Совпадает: {s['match']}   |   "
            f"Только в A: {s['only_a']}   |   Только в B: {s['only_b']}   |   "
            f"Разные типы: {s['type_diff']}"
        )

    def _sync_expand(self, item, expand):
        path = self._item_path(item)
        for tw in (self.tree_widget_a, self.tree_widget_b):
            target = self._find_by_path(tw, path)
            if target and target is not item:
                target.setExpanded(expand)

    def _item_path(self, item):
        path = []
        while item and item.parent():
            path.insert(0, item.parent().indexOfChild(item))
            item = item.parent()
        return path

    def _find_by_path(self, tw, path):
        item = tw.invisibleRootItem()
        for idx in path:
            if idx >= item.childCount():
                return None
            item = item.child(idx)
        return item

    def _on_item_clicked(self, item, column):
        full = item.data(0, QtCore.Qt.UserRole)
        if full and cmds.objExists(full):
            cmds.select(full, replace=True)

    def _show_only_diff(self):
        self._filter_tree(self.tree_widget_a.invisibleRootItem(), only_diff=True)
        self._filter_tree(self.tree_widget_b.invisibleRootItem(), only_diff=True)
        self.tree_widget_a.expandAll()
        self.tree_widget_b.expandAll()

    def _show_all(self):
        self._filter_tree(self.tree_widget_a.invisibleRootItem(), only_diff=False)
        self._filter_tree(self.tree_widget_b.invisibleRootItem(), only_diff=False)

    def _filter_tree(self, item, only_diff):
        has_diff_descendant = False
        for i in range(item.childCount()):
            child = item.child(i)
            child_has_diff = self._filter_tree(child, only_diff)
            status = child.data(0, QtCore.Qt.UserRole + 1)
            is_diff = status in ('only_a', 'only_b', 'type_diff')

            if only_diff:
                child.setHidden(not (is_diff or child_has_diff))
            else:
                child.setHidden(False)

            if is_diff or child_has_diff:
                has_diff_descendant = True

        return has_diff_descendant


_diff_window = None


def show_diff(root_a=None, root_b=None):
    global _diff_window

    if root_a is None or root_b is None:
        sel = cmds.ls(selection=True, long=True)
        if len(sel) != 2:
            cmds.warning("Выдели ровно 2 объекта для сравнения")
            return
        root_a, root_b = sel[0], sel[1]

    tree_a = get_tree(root_a)
    tree_b = get_tree(root_b)

    if tree_a is None or tree_b is None:
        cmds.warning("Не удалось построить дерево")
        return

    name_a = strip_ns(root_a)
    name_b = strip_ns(root_b)

    try:
        if _diff_window:
            _diff_window.close()
    except Exception:
        pass

    _diff_window = HierarchyDiffUI(tree_a, tree_b, name_a, name_b)
    _diff_window.show()


show_diff()