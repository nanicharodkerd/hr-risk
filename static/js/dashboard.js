/*global*/
let selectedJobs = []
let charts = {}

const regionSelect = document.getElementById("regionSelect")
const provinceSelect = document.getElementById("provinceSelect")
const statusSelect = document.getElementById("statusSelect")

/*filter*/
function toggleJob(job, el){

  if(selectedJobs.includes(job) && selectedJobs.length === 1){
    return
  }

  el.classList.toggle("active")

  if(selectedJobs.includes(job)){
    selectedJobs = selectedJobs.filter(j=>j!==job)
  }else{
    selectedJobs.push(job)
  }

  applyFilter()
}


/* โหลดจังหวัดตามเขต */
regionSelect.addEventListener("change", ()=>{

  fetch(`/api/provinces?region=${regionSelect.value}`)
    .then(r=>r.json())
    .then(ps=>{

      provinceSelect.innerHTML = '<option value="">ทั้งหมด</option>'

      ps.forEach(p=>{
        provinceSelect.innerHTML += `<option value="${p}">${p}</option>`
      })

    })
})

/* init job filter default */
window.addEventListener("DOMContentLoaded", ()=>{

  const jobButtons = document.querySelectorAll(".job-btn")

  selectedJobs = []   // กันค่าซ้ำ

  jobButtons.forEach(btn=>{

    const job = btn.dataset.job

    selectedJobs.push(job)
    btn.classList.add("active")

  })

  applyFilter()

})

/*apply filter */
function applyFilter(){

  const q = []

  if(selectedJobs.length) q.push("job="+selectedJobs.join(","))
  if(regionSelect.value) q.push("region="+regionSelect.value)
  if(provinceSelect.value) q.push("province="+provinceSelect.value)
  if(statusSelect.value) q.push("status="+statusSelect.value)

  fetch("/api/dashboard?"+q.join("&"))
    .then(r=>r.json())
    .then(d=>{
      renderKPI(d.kpi)
      renderCharts(d)
    })
}

/*kpi*/
function renderKPI(k){

  document.getElementById("kpi-total").innerText =
    (k.total || 0).toLocaleString() + " คน"

  document.getElementById("kpi-occupied").innerText =
    (k.occupied || 0).toLocaleString() + " คน"

  document.getElementById("kpi-vacant").innerText =
    (k.vacant || 0).toLocaleString() + " คน"

  document.getElementById("kpi-salary").innerText =
    (k.avg_salary || 0).toLocaleString() + " บาท"
}

/*chart helper*/
function drawChart(id, config){

  if(!config.data.labels.length) return

  config.options = {
    responsive:true,
    maintainAspectRatio:false
  }

  charts[id]?.destroy()

  charts[id] = new Chart(
    document.getElementById(id),
    config
  )
}

/*chart region*/
function renderRegionChart(d){

  const regionVal = regionSelect.value
  const provinceVal = provinceSelect.value

  // ไม่เลือกเขต 13 เขต
  if(!regionVal){
    drawChart("chartRegion",{
      type:"bar",
      data:{
        labels:Object.keys(d.overview.region || {}).map(r=>"เขต "+r),
        datasets:[{
          label:"จำนวนบุคลากร",
          data:Object.values(d.overview.region || {})
        }]
      }
    })
    return
  }

  // เลือกเขต รายจังหวัด
  if(regionVal && !provinceVal){
    drawChart("chartRegion",{
      type:"bar",
      data:{
        labels:Object.keys(d.overview.province || {}),
        datasets:[{
          label:"จำนวนบุคลากร",
          data:Object.values(d.overview.province || {})
        }]
      }
    })
    return
  }

  //เลือกจังหวัดเดียว แท่งเดียว
  drawChart("chartRegion",{
    type:"bar",
    data:{
      labels:[provinceVal],
      datasets:[{
        label:"จำนวนบุคลากร",
        data:[d.kpi.total]
      }]
    }
  })
}

/*chart*/
function renderCharts(d){

  if(d.overview?.region){
    renderRegionChart(d)
  }


  if(d.overview?.gender){
        drawChart("chartGender",{
        type:"doughnut",
            data:{
                labels:Object.keys(d.overview.gender),
                datasets:[{
                data:Object.values(d.overview.gender)}]
            }
        })
        document.getElementById("femaleCount").innerText =
        (d.overview.gender["หญิง"] || 0) + " คน"

        document.getElementById("maleCount").innerText =
        (d.overview.gender["ชาย"] || 0) + " คน"
  }

  if(d.overview?.job){
        drawChart("chartJob",{
        type:"bar",
            data:{
                labels:Object.keys(d.overview.job),
                datasets:[{
                        data:Object.values(d.overview.job) ,
                        backgroundColor:["#4CAF50","#2196F3","#FFC107","#FF5722","#9C27B0","#009688","#795548"]}]
            }
        })
  }

     if(d.overview?.age){
       drawChart("chartAge",{
         type:"bar",
         data:{
           labels:Object.keys(d.overview.age),
           datasets:[{
                data:Object.values(d.overview.age) ,
                backgroundColor:["#4CAF50","#2196F3","#FFC107","#FF5722","#9C27B0","#009688","#795548"]}]
         }
       })
     }

     if(d.overview?.status){
     drawChart("chartStatus",{
       type:"bar",
       data:{
         labels:Object.keys(d.overview.status),
         datasets:[{
                data:Object.values(d.overview.status) ,
                backgroundColor:["#4CAF50","#2196F3","#FFC107","#FF5722","#9C27B0","#009688","#795548"]}]
       }
     })
   }

   if(d.overview?.retire){
   drawChart("chartRetire",{
       type:"bar",
       data:{
         labels:Object.keys(d.overview.retire),
         datasets:[{
                data:Object.values(d.overview.retire),
                backgroundColor:["#4CAF50","#2196F3","#FFC107","#FF5722","#9C27B0","#009688","#795548"] }]
         }
      })
   }

   if(d.overview?.job_level){
     const labels = Object.keys(d.overview.job_level)
        .filter(k => k && k !== "nan")

     const values = labels.map(k => d.overview.job_level[k])

     drawChart("chartJobLevel",{
         type:"bar",
         data:{
             labels: labels,
                datasets:[{
                data: values ,
                backgroundColor:["#4CAF50","#2196F3","#FFC107","#FF5722","#9C27B0","#009688","#795548"]}]
         }
     })
   }

   if(d.overview?.agency_type){
    drawChart("chartAgency",{
       type:"bar",
       data:{
           labels:Object.keys(d.overview.agency_type),
           datasets:[{
                data:Object.values(d.overview.agency_type),
                backgroundColor:["#4CAF50","#2196F3","#FFC107","#FF5722","#9C27B0","#009688","#795548"]
                }]
           }
       })
   }
}
