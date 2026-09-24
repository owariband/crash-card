# 面试自测：为什么 InnoDB 索引适合 B+ 结构？

先停在第一张，用自己的话解释内部节点、记录载荷与页式存储之间的关系，再滑到第二张核对。

不用背固定措辞：重点是说明为什么、什么条件下成立。范围为 MySQL 8.4 InnoDB 普通 BTREE 索引。

#MySQL #数据库索引 #B树 #B加树 #面试复习

## 参考资料

- [CMU 15-445/645 (2024) — Indexes & Filters I](https://15445.courses.cs.cmu.edu/fall2024/notes/08-indexes1.pdf)
- [Dave Mount (2019) — B Trees](https://www.cs.umd.edu/class/fall2019/cmsc420-0201/Lects/slides-09-btree.pdf)
- [MySQL 8.4 — Physical Structure of an InnoDB Index](https://dev.mysql.com/doc/refman/8.4/en/innodb-physical-structure.html)
