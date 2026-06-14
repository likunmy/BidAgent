import axios from 'axios'

const request = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

export default request
