// ****************************************************************************
//
///  @filename: test-producer.cpp
///
///  @author: D. Reitz
///
///  @date: 19-Sept-2012
///
///  @summary: Example C++ test using the AmqClient 
/// 
// *****************************************************************************

#include "AmqClient.h"
#include <unistd.h>
int main (void)
{
   std::string uri = "failover://(tcp://heidelberg:61616,tcp://drembpro-vnet:61616)?randomize=false";
   Adara::Utils::AmqClient amqc(uri, "icat", "icat");
   for (int i=31526; i<31527; ++i)
   { 
      Adara::Utils::RunInfo ri("IPTS-5678", "HYSA", i, "the-file-name"); 
      amqc.send("TRANSLATION.STARTED", ri);
      amqc.send("TRANSLATION.COMPLETE", ri);
      amqc.send("REDUCTION.DATA_READY", ri);
      amqc.send("CATALOG.DATA_READY", ri);
      sleep(1);
   }
   return 0;
}
