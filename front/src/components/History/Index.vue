<template>
  <div class="layout">
    <Row style="padding: 10px 10px 10px 23px;">
      <div class="search-con search-con-top">
        <Input v-model="query.keyword" placeholder="查询内容" style="width: 200px"/>
        <Button type="primary" class="search-btn" @click="search()" style="margin-left: 10px">
          <Icon type="search"/>
          查询
        </Button>
      </div>
    </Row>
    <Row style="padding: 10px 10px 10px 23px;">
      <iCol span="8">
        <Menu mode="horizontal" :active-name="query.type">
          <MenuItem @click.native="search('all')" name="all">全部</MenuItem>
          <MenuItem @click.native="search('logger')" name="logger">logger</MenuItem>
          <MenuItem @click.native="search('repeater')" name="repeater">repeater</MenuItem>
          <MenuItem @click.native="search('apis')" name="apis">apis</MenuItem>
        </Menu>
      </iCol>
    </Row>
    <Row style="padding: 5px 25px;min-height:400px;display: block;background-color:#FFFFFF; margin:0 23px">
      <Table
          highlight-row
          :loading="table.loading"
          :show-header="false"
          :columns="table.headers"
          :data="table.body"
          @on-row-click="redirectRepeater"
      ></Table>
    </Row>
    <Row style="padding: 5px 25px;">
      <Layout style="background-color: #F1F1F1;">
        <Page
            :total="table.tableCount"
            show-sizer
            show-elevator
            transfer
            @on-change="getPageNumber"
            @on-page-size-change="getPageSize"
        />
      </Layout>
    </Row>
    <Row style="padding: 5px 25px">
      <iCol span="8">
                <span v-if="query.type === 'all'"
                >总共查询结果为: {{ table.tableCount }}条, logger条数: {{ table.loggerCount }}, repeater条数:
                    {{ table.repeaterCount }}, apis条数: {{ table.apisCount }}</span
                >
        <span v-else>总共查询结果为: {{ table.tableCount }}条</span>
      </iCol>
    </Row>
  </div>
</template>

<script>
import {getSearchHistoryData} from "@/utils/api";

export default {
  name: "history-index",
  data: () => {
    return {
      table: {
        headers: [
          {
            title: "结果",
            key: "data",
            render: (h, params) => {
              let req = params.row.data.request;
              let resp = params.row.data.response;
              let title = req.scheme + "://" + req.host + req.path;
              let reqContent = req.content || "";
              let cookie = req.headers.cookie || req.headers.Cookie || "";
              let respContent = resp.content || "";
              let dt = resp.timestamp_start || "";
              let statusCode = resp.status_code || "";
              if (dt) {
                dt = new Date(dt * 1000 + 8 * 3600 * 1000);
                dt = dt.toJSON();
                dt = dt.replace("T", " ");
                dt = dt.replace("Z", "");
              }
              return h(
                  "div",
                  {
                    style: {
                      padding: "10px",
                    },
                  },
                  [
                    h(
                        "p",
                        {
                          style: {
                            "font-size": "10px",
                          },
                        },
                        [h("span", params.row.data.type)]
                    ),
                    h(
                        "p",
                        {
                          style: {
                            padding: "10px",
                          },
                        },
                        [
                          h("div", [
                            h("strong", title),
                            h(
                                "div",
                                {
                                  style: {
                                    float: "right",
                                  },
                                },
                                [
                                  h("strong", dt),
                                  h(
                                      "strong",
                                      {
                                        style: {
                                          "padding-left": "30px",
                                        },
                                      },
                                      statusCode
                                  ),
                                ]
                            ),
                          ]),
                        ]
                    ),
                    h(
                        "p",
                        {
                          style: {
                            padding: "10px",
                          },
                        },
                        [h("span", cookie.slice(0, 200))]
                    ),
                    h(
                        "p",
                        {
                          style: {
                            padding: "10px",
                          },
                        },
                        [h("span", reqContent.slice(0, 200))]
                    ),
                    h(
                        "p",
                        {
                          style: {
                            padding: "10px",
                          },
                        },
                        [h("span", respContent.slice(0, 200))]
                    ),
                  ]
              );
            },
          },
        ],
        body: [],
        tableCount: 0,
        loggerCount: 0,
        repeaterCount: 0,
        apisCount: 0,
        loading: false,
      },
      query: {
        keyword: "",
        type: "all",
        page: 1,
        size: 10,
      },
    }
  },
  methods: {
    redirectRepeater: function (row) {
      let uri = window.location.origin.toString() + "/#/repeater?id=" + row.data.request._id;
      window.open(uri);
    },
    respToTableData: function (resp) {
      for (let item of resp) {
        this.table.body.push({
          data: item,
        });
      }
    },
    setTableData: function () {
      let _this = this;
      _this.table.body = [];
      _this.table.loading = true;
      getSearchHistoryData(this.query)
          .then((resp) => {
            let respBody = resp.data.data.data;
            _this.respToTableData(respBody.data);
            _this.table.tableCount = respBody.count;
            _this.table.loggerCount = respBody.logger_count;
            _this.table.repeaterCount = respBody.repeater_count;
            _this.table.apisCount = respBody.apis_count;
            _this.table.loading = false;
          })
          .catch((err) => {
            _this.table.loading = false;
            _this.$Notice.error({
              title: "查询异常",
              desc: err
            });
          });
    },
    search: function (type) {
      if (type) {
        this.query.type = type;
      }
      this.query.size = 10;
      this.query.page = 1;
      this.setTableData();
    },
    getPageNumber: function (page) {
      this.query.page = page;
      this.setTableData();
    },
    getPageSize: function (size) {
      this.query.size = size;
      this.setTableData();
    },
  },
  mounted() {
  }
}
</script>

<style scoped>
.ivu-btn-primary {
  background-color: #547EFF;
}
</style>