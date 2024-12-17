
document.addEventListener('DOMContentLoaded',()=>{

const fish = document.querySelector('#fish');

const Spinning = [
    { transform: "rotate(0) scale(1)" },
    { transform: "rotate(360deg) scale(0)" },
  ];
  
  const Timing = {
    duration: 2000,
    iterations: 1,
  };
  
  fish.animate(Spinning,Timing );







});
