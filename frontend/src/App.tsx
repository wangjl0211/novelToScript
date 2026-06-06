import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import {
  SettingOutlined,
  HomeOutlined,
} from '@ant-design/icons';
import { Link, useLocation } from 'react-router-dom';
import ProjectList from './pages/ProjectList';
import ProjectWorkspace from './pages/ProjectWorkspace';
import Settings from './pages/Settings';

const { Header, Content } = Layout;

function AppLayout() {
  const location = useLocation();
  const selected = location.pathname.startsWith('/settings')
    ? 'settings'
    : location.pathname.startsWith('/project')
      ? 'projects'
      : 'home';

  return (
    <Layout className="app-layout">
      <Header style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
        <div style={{ color: '#fff', fontSize: 18, fontWeight: 600 }}>
          NovelToScript
        </div>
        <Menu
          theme="dark"
          mode="horizontal"
          selectedKeys={[selected]}
          style={{ flex: 1, minWidth: 0 }}
          items={[
            { key: 'home', icon: <HomeOutlined />, label: <Link to="/">项目列表</Link> },
            { key: 'settings', icon: <SettingOutlined />, label: <Link to="/settings">设置</Link> },
          ]}
        />
      </Header>
      <Content className="content-area">
        <Routes>
          <Route path="/" element={<ProjectList />} />
          <Route path="/project/:id/*" element={<ProjectWorkspace />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Content>
    </Layout>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppLayout />
    </BrowserRouter>
  );
}
