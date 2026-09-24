# B+ 树点查一定更快？三层就读三次磁盘？

这次把辨错与解答放在同一期。先分别修正两条推论，再滑到第二张核对理由。

区分结构特点、逻辑页访问和物理读盘，才能把性能结论说准确。本期是结构推理，不是跑分结果；数据库背景为 MySQL 8.4 InnoDB。

#MySQL #数据库索引 #B树 #B加树 #面试复习

## 参考资料

- [CMU 15-445/645 (2024) — Indexes & Filters I](https://15445.courses.cs.cmu.edu/fall2024/notes/08-indexes1.pdf)
- [Dave Mount (2019) — B Trees](https://www.cs.umd.edu/class/fall2019/cmsc420-0201/Lects/slides-09-btree.pdf)
- [MySQL 8.4 — Buffer Pool](https://dev.mysql.com/doc/refman/8.4/en/innodb-buffer-pool.html)
- [MySQL 8.4 — Clustered and Secondary Indexes](https://dev.mysql.com/doc/refman/8.4/en/innodb-index-types.html)
