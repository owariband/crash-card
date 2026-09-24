# 范围查询怎样从起点走到终点？

假定查询选择 age 二级索引，条件是 20≤age<30。这张流程卡把首次定位、页内扫描、跨页和停止条件串起来。

只追踪索引键，不展开取行和事务可见性检查。逻辑上的叶页相邻，不等于磁盘位置连续。适用背景：MySQL 8.4 InnoDB。

#MySQL #数据库索引 #B树 #B加树 #面试复习

## 参考资料

- [CMU 15-445/645 (2024) — Indexes & Filters I](https://15445.courses.cs.cmu.edu/fall2024/notes/08-indexes1.pdf)
- [MySQL mysql-8.4.0 — btr0btr.cc](https://github.com/mysql/mysql-server/blob/mysql-8.4.0/storage/innobase/btr/btr0btr.cc)
- [MySQL 8.4 — Clustered and Secondary Indexes](https://dev.mysql.com/doc/refman/8.4/en/innodb-index-types.html)
