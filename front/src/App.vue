<template>
  <div class="layout">
    <Layout style="background: #F1F1F1;">
      <Header style="background: #333333;">
        <Menu mode="horizontal" theme="dark" :active-name="$route.name" style="background: #333333; height:64px;">
          <div v-for="(item, index) in routes" :key="index" :name="item.name" :to="item.path">
            <MenuItem :name="item.name" :to="item.path" v-if="item.isTheme">
              <h1>{{ item.title || item.name }}</h1>
            </MenuItem>
            <Submenu :name="item.name" :to="item.path" v-else-if="item.groups">
              <template slot="title">
                <h3 style="display: initial">{{ item.title || item.name }}</h3>
              </template>
              <MenuGroup v-if="item.groups.group" :title="item.groups.group.title">
                <MenuItem
                    v-for="(subItem, index) in item.groups.group"
                    :key="index"
                    :name="subItem.name"
                    :to="subItem.path"
                >
                  <h4>{{ subItem.title || subItem.name }}</h4>
                </MenuItem>
              </MenuGroup>
              <MenuItem
                  v-else
                  v-for="(subItem, index) in item.groups"
                  :key="index"
                  :name="subItem.name"
                  :to="subItem.path"
              >
                <h4>{{ subItem.title || subItem.name }}</h4>
              </MenuItem>
            </Submenu>
            <MenuItem :name="item.name" :to="item.path" style="height:64px;" v-else>
              <h3>{{ item.title || item.name }}</h3>
            </MenuItem>
          </div>
          <div>
            <a href="/api/logout">
              <MenuItem style="float: right" name="logout">
                <h3>退出</h3>
              </MenuItem>
            </a>
            <MenuItem
                style="float: right; padding-right: 5px"
                name="show-username"
            >admin
            </MenuItem
            >
          </div>
        </Menu>
      </Header>
      <Row style="display: block">
        <Affix :offset-top="windowHeight" style="position: fixed; z-index: 10;">
          <div style="text-align: center">
            <Row>
              <Button
                  type="primary"
                  size="small"
                  style="height: auto; padding: 1px;border-radius:0;background-color:#547EFF;"
                  @mouseenter.native="showDrawer = true"
              >
                <span style="writing-mode: vertical-rl; margin-top:3px;">准入代理</span>
              </Button>
            </Row>
          </div>
        </Affix>
        <Content :style="{ padding: '10px' }">
          <router-view></router-view>
        </Content>
      </Row>

      <MainConnList
          :show="showDrawer"
          @setDrawerStatus="
                    (status) => {
                        this.showDrawer = status;
                    }
                "
      ></MainConnList>
    </Layout>
  </div>
</template>

<script>

import routes from "./router";
import MainConnList from "./components/MainConnDrawer";

export default {
  name: 'App',
  components: {
    MainConnList,
  },
  data: () => {
    return {
      routes: routes,
      windowHeight: 140,
      showDrawer: false,
    }
  },
  methods: {
    setAffixHeight: function () {
      let height = document.documentElement.clientHeight || document.body.clientHeight;
      height = (height - 20) * 0.3;
      if (height > 140) {
        this.windowHeight = height;
      }
    },
  },
  mounted() {
    this.setAffixHeight();
    window.onresize = () => {
      this.setAffixHeight();
    };
  },

}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  margin-top: 60px;
}
</style>
