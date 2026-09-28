import struct
import os

PAGE_SIZE = 4096
# Row format: ID (int: 4 bytes) + Title (char[256]) + Completed (bool: 1 byte)
ROW_FORMAT = "<I256s?"
ROW_SIZE = struct.calcsize(ROW_FORMAT)  # 261 bytes

# Leaf Node Header: node_type (1B), is_root (1B), num_cells (2B)
HEADER_FORMAT = "<BBH"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
CELL_SIZE = 4 + ROW_SIZE  # 4-byte key + serialized row
MAX_CELLS = (PAGE_SIZE - HEADER_SIZE) // CELL_SIZE


class Pager:
    def __init__(self, filename="todos.db"):
        self.filename = filename
        self.file = open(filename, "a+b")
        self.file.seek(0, os.SEEK_END)
        self.file_length = self.file.tell()
        self.pages = {}

    def get_page(self, page_num):
        if page_num in self.pages:
            return self.pages[page_num]

        # Read page from disk or initialize empty page
        self.file.seek(page_num * PAGE_SIZE)
        page_bytes = self.file.read(PAGE_SIZE)
        if len(page_bytes) < PAGE_SIZE:
            page = bytearray(PAGE_SIZE)
            # Default header: type=LEAF(1), is_root=1, num_cells=0
            struct.pack_into(HEADER_FORMAT, page, 0, 1, 1, 0)
        else:
            page = bytearray(page_bytes)

        self.pages[page_num] = page
        return page

    def flush_page(self, page_num):
        if page_num in self.pages:
            self.file.seek(page_num * PAGE_SIZE)
            self.file.write(self.pages[page_num])
            self.file.flush()


class SimpleDB:
    def __init__(self, filename="todos.db"):
        self.pager = Pager(filename)
        self.root_page_num = 0

    def _read_header(self, page):
        return struct.unpack_from(HEADER_FORMAT, page, 0)

    def _write_header(self, page, node_type, is_root, num_cells):
        struct.pack_into(HEADER_FORMAT, page, 0, node_type, is_root, num_cells)

    def _cell_offset(self, index):
        return HEADER_SIZE + (index * CELL_SIZE)

    def select_all(self):
        page = self.pager.get_page(self.root_page_num)
        _, _, num_cells = self._read_header(page)
        rows = []
        for i in range(num_cells):
            offset = self._cell_offset(i)
            key, todo_id, title_raw, completed = struct.unpack_from(
                "<I" + ROW_FORMAT[1:], page, offset
            )
            title = title_raw.decode("utf-8").rstrip("\x00")
            rows.append({"id": todo_id, "title": title, "completed": completed})
        return rows

    def insert(self, todo_id, title, completed=False):
        page = self.pager.get_page(self.root_page_num)
        node_type, is_root, num_cells = self._read_header(page)

        if num_cells >= MAX_CELLS:
            raise RuntimeError("Page full! (Leaf split required)")

        # Find position using binary search (Connor Stack - Part 9)
        low, high = 0, num_cells
        while low < high:
            mid = (low + high) // 2
            mid_key = struct.unpack_from("<I", page, self._cell_offset(mid))[0]
            if mid_key == todo_id:
                raise ValueError("Duplicate key")
            elif mid_key < todo_id:
                low = mid + 1
            else:
                high = mid
        pos = low

        # Shift cells right to make room
        for i in range(num_cells, pos, -1):
            src = self._cell_offset(i - 1)
            dst = self._cell_offset(i)
            page[dst:dst + CELL_SIZE] = page[src:src + CELL_SIZE]

        # Pack and write new cell
        title_bytes = title.encode("utf-8")[:256].ljust(256, b"\x00")
        offset = self._cell_offset(pos)
        struct.pack_into(
            "<I" + ROW_FORMAT[1:],
            page,
            offset,
            todo_id,
            todo_id,
            title_bytes,
            completed,
        )

        # Update cell count & flush page to disk
        self._write_header(page, node_type, is_root, num_cells + 1)
        self.pager.flush_page(self.root_page_num)

    def update_completed(self, todo_id, completed):
        page = self.pager.get_page(self.root_page_num)
        _, _, num_cells = self._read_header(page)
        for i in range(num_cells):
            offset = self._cell_offset(i)
            key = struct.unpack_from("<I", page, offset)[0]
            if key == todo_id:
                # Update completed byte (offset + 4(key) + 4(id) + 256(title))
                struct.pack_into("?", page, offset + 4 + 4 + 256, completed)
                self.pager.flush_page(self.root_page_num)
                return True
        return False

    def delete(self, todo_id):
        page = self.pager.get_page(self.root_page_num)
        node_type, is_root, num_cells = self._read_header(page)
        for i in range(num_cells):
            offset = self._cell_offset(i)
            key = struct.unpack_from("<I", page, offset)[0]
            if key == todo_id:
                # Shift subsequent cells left
                for j in range(i, num_cells - 1):
                    src = self._cell_offset(j + 1)
                    dst = self._cell_offset(j)
                    page[dst:dst + CELL_SIZE] = page[src:src + CELL_SIZE]
                self._write_header(page, node_type, is_root, num_cells - 1)
                self.pager.flush_page(self.root_page_num)
                return True
        return False
