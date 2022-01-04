<style scoped>
.demo-drawer-profile {
  font-size: 14px;
}

.demo-drawer-profile .ivu-col {
  margin-bottom: 12px;
}
</style>

<template>
  <div>
    <Drawer v-model="showDrawer" width="640" :scrollable="true" placement="left">
      <div class="demo-drawer-profile">
        <Row :style="{ 'padding-top': '30px' }">
          <Table :columns="table.header" :data="table.body" width="600">
            <template slot-scope="{ row }" slot="opt">
              <Button
                  :loading="connLoading"
                  @click="optConnStatus(row.ip, 'open')"
                  type="success"
                  size="small"
                  v-if="row.status === '未接入'"
              >接入
              </Button
              >
              <Button
                  :loading="connLoading"
                  @click="optConnStatus(row.ip, 'close')"
                  type="error"
                  size="small"
                  v-if="row.status === '已接入'"
              >撤销
              </Button
              >
              <span v-else></span>
            </template>
          </Table>
        </Row>
      </div>
    </Drawer>
  </div>
</template>

<script>
import {getConnIp, setConnIp, releaseConnIp} from "@/utils/api";

export default {
  name: "MainConnList",
  props: ["show"],
  data: function () {
    return {
      connLoading: false,
      table: {
        header: [
          {
            title: "IP",
            key: "ip",
          },
          {
            title: "状态",
            key: "status",
          },
          {
            title: "拦截状态",
            key: "intercept_status",
          },
          {
            title: "操作",
            slot: "opt",
          },
        ],
        body: [],
      },
    };
  },
  methods: {
    optConnStatus(ip, status) {
      let _this = this;
      _this.connLoading = true;
      if (status === "open") {
        setConnIp(ip)
            .then(() => {
              _this.connLoading = false;
              _this.loadTable();
            })
            .catch((e) => {
              _this.connLoading = false;
              _this.$Message.warning(`设置代理ip失败: ${e}`);
            });
      } else {
        releaseConnIp(ip)
            .then(() => {
              _this.connLoading = false;
              _this.loadTable();
            })
            .catch((e) => {
              _this.connLoading = false;
              _this.$Message.warning(`撤销代理ip失败: ${e}`);
            });
      }
    },
    loadTable() {
      let _this = this;
      getConnIp()
          .then((resp) => {
            let body = [];
            for (let [key, value] of Object.entries(resp.data.data)) {
              let obj = !value || value === "null" ? {status: 0} : JSON.parse(value);
              body.push({
                ip: key,
                status: obj.status === 1 ? "已接入" : "未接入",
                intercept_status: obj.intercept_status === 1 ? "已开启" : "未开启",
                user: obj.user_name || "-",
              });
            }
            _this.table.body = body;
          })
          .catch((e) => {
            _this.$Message.warning(`获取链接ip失败: ${e}`);
          });
    },
  },
  computed: {
    showDrawer: {
      set(value) {
        this.$emit("setDrawerStatus", value);
      },
      get() {
        return this.show;
      },
    },
  },
  watch: {
    show: function (value) {
      if (value) {
        this.loadTable();
      }
    },
  },
};
</script>
