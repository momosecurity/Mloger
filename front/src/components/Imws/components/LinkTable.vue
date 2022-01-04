<template>
  <div>
    <Card :bordered="true">
      <p slot="title">连接列表</p>
      <p slot="extra">
                <span>存活: {{ liveCnt }}</span
                ><span style="padding-left: 10px">断开: {{ dieCnt }}</span>
      </p>
      <Table
          highlight-row
          :columns="table.headers"
          :data="table.body"
          height="590"
          @on-row-click="showConn"
      ></Table>
    </Card>
  </div>
</template>

<script>
export default {
  name: "LinkTable",
  props: ["linkData", "ip"],
  data: () => {
    return {
      table: {
        headers: [
          {
            title: "存活",
            key: "live",
            align: "center",
            render: (h, params) => {
              return h(
                  "Tag",
                  {
                    props: {
                      color: params.row.live ? "success" : "error",
                    },
                    style: {
                      border: "none !important",
                      width: "16px",
                      height: "16px",
                      "-moz-border-radius": "8px",
                      "-webkit-border-radius": "8px",
                      "border-radius": "8px",
                    },
                  },
                  ""
              );
            },
          },
          {
            title: "连接",
            key: "link",
            align: "center",
            width: "200",
          },
          {
            title: "类型",
            key: "type",
            align: "center",
            width: "105",
          },
        ],
        body: [],
      },
      total_conn_data: {body: [], sort_list: []},
      liveCnt: 0,
      dieCnt: 0,
      select_pk: "",
    };
  },
  methods: {
    refreshTable: function () {
      if (!Object.keys(this.linkData).length) {
        this.dieCnt = this.liveCnt = 0;
        this.total_conn_data.body = [];
        this.total_conn_data.sort_list = [];
        return;
      }
      this.dieCnt = this.liveCnt = 0;
      for (let [k, v] of Object.entries(this.linkData)) {
        let idx = this.total_conn_data.sort_list.indexOf(k);
        let tmp = {
          live: v.live || false,
          link: `${v.server_host}:${v.server_port}` || "-",
          type: v.type || "-",
          pk: v._id,
          raw_data: v,
        };
        if (idx < 0) {
          this.total_conn_data.sort_list.unshift(k);
          this.total_conn_data.body.unshift(tmp);
        } else {
          this.total_conn_data.body[idx] = tmp;
        }
      }
      let body = [];
      for (let item of this.total_conn_data.body) {
        if (item.raw_data.client_host && !item.raw_data.client_host.includes(this.ip)) {
          continue;
        }
        if (item.live) {
          this.liveCnt++;
        } else {
          this.dieCnt++;
        }
        item._highlight = item.pk === this.select_pk;
        body.push(item);
      }
      this.table.body = body;
    },
    showConn: function (row) {
      this.select_pk = row.pk;
      this.$emit("showConnDetail", row.pk);
    },
  },
  mounted() {
    this._linkTable = setInterval(this.refreshTable, 1000);
  },
};
</script>
